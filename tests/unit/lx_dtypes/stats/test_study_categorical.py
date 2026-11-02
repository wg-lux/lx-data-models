import math

import numpy as np
import pytest
from pydantic import ValidationError
from scipy import stats
from scipy.stats.contingency import odds_ratio, relative_risk

from lx_dtypes.models.contracts.study_analysis import PlotState, StudyCategorical
from lx_dtypes.stats.study_categorical import (
    CategoricalObservation,
    evaluate_categorical,
)


def config(method: object = "fisher_exact", **overrides: object) -> StudyCategorical:
    return StudyCategorical.model_validate(
        {
            "name": "comparison",
            "method": method,
            "endpoint": "disease",
            "groups": ["exposed", "control"],
            "design": "cohort",
            **overrides,
        }
    )


def observations(
    table: list[list[int]], diagnostic: bool = False
) -> list[CategoricalObservation]:
    result: list[CategoricalObservation] = []
    for i, row in enumerate(table):
        for j, count in enumerate(row):
            for _ in range(count):
                states: dict[str, PlotState] = {
                    "disease": "positive" if j == 0 else "negative"
                }
                if diagnostic:
                    states = {
                        "disease": "positive" if i == 0 else "negative",
                        "reference": "positive" if j == 0 else "negative",
                    }
                result.append(
                    CategoricalObservation(
                        str(len(result)), ["exposed", "control"][i], states
                    )
                )
    return result


@pytest.mark.parametrize("method", ["fisher_exact", "chi_square"])
def test_comparison_matches_scipy_and_preserves_orientation(method: str) -> None:
    table = [[30, 20], [10, 40]]
    result = evaluate_categorical(config(method), observations(table))
    assert result.table == table
    assert result.rows == ["exposed", "control"]
    expected = (
        stats.fisher_exact(np.asarray(table))
        if method == "fisher_exact"
        else stats.chi2_contingency(table, correction=False)
    )
    assert result.p == pytest.approx(expected.pvalue)
    odds, risk = result.estimates
    expected_odds = odds_ratio(table, kind="conditional")
    assert odds.value == pytest.approx(expected_odds.statistic)
    assert odds.low == pytest.approx(expected_odds.confidence_interval().low)
    assert risk.value == pytest.approx(3)
    assert risk.high == pytest.approx(
        relative_risk(30, 50, 10, 50).confidence_interval().high
    )
    reverse = evaluate_categorical(
        config(method, groups=["control", "exposed"]), observations(table)
    )
    assert reverse.estimates[1].value == pytest.approx(1 / 3)
    assert odds.value is not None
    assert reverse.estimates[0].value == pytest.approx(1 / odds.value)
    case_control = evaluate_categorical(
        config(method, design="case_control"), observations(table)
    )
    assert [e.term for e in case_control.estimates] == ["odds_ratio"]


def test_diagnostic_pair_uses_same_patient_and_wilson_intervals() -> None:
    result = evaluate_categorical(
        config("diagnostic_accuracy", groups=[], design=None, reference="reference"),
        observations([[80, 10], [20, 90]], True),
    )
    assert result.p is None and result.df is None
    assert result.table == [[80, 10], [20, 90]]
    assert result.observations == 200
    estimates = {e.term: e for e in result.estimates}
    assert estimates["sensitivity"].value == pytest.approx(0.8)
    assert estimates["specificity"].value == pytest.approx(0.9)
    assert estimates["positive_predictive_value"].value == pytest.approx(80 / 90)
    assert estimates["negative_predictive_value"].value == pytest.approx(90 / 110)
    assert estimates["accuracy"].value == pytest.approx(0.85)
    ci = stats.binomtest(80, 100).proportion_ci(method="wilson")
    assert estimates["sensitivity"].low == pytest.approx(ci.low)


@pytest.mark.parametrize(
    "state", ["missing", "conflicting", "ineligible", "eligibility_unknown"]
)
def test_unknown_is_never_negative_and_requires_explicit_exclusion(
    state: PlotState,
) -> None:
    rows = observations([[3, 2], [1, 4]]) + [
        CategoricalObservation("extra", "exposed", {"disease": state})
    ]
    with pytest.raises(ValueError, match="complete_case"):
        evaluate_categorical(config(), rows)
    result = evaluate_categorical(config(missing="complete_case"), rows)
    assert result.excluded == 1 and result.observations == 10
    assert result.table == [[3, 2], [1, 4]]


def test_repeated_patients_and_absent_variables_fail_before_exclusion() -> None:
    rows = observations([[3, 2], [1, 4]])
    with pytest.raises(ValueError, match="one analysis unit"):
        evaluate_categorical(config(), rows + rows[:1])
    with pytest.raises(ValueError, match="missing a configured endpoint"):
        evaluate_categorical(
            config(missing="complete_case"),
            [CategoricalObservation("other", "exposed", {})],
        )


def test_sparse_chi_square_is_not_silently_switched_or_corrected() -> None:
    rows = observations([[1, 9], [8, 2]])
    with pytest.raises(ValueError, match="configure fisher_exact"):
        evaluate_categorical(config("chi_square"), rows)
    assert evaluate_categorical(config(), rows).p == pytest.approx(0.005477494641581329)


@pytest.mark.parametrize("table", [[[0, 10], [10, 0]], [[10, 0], [0, 10]]])
def test_zero_cells_remain_explicit_and_json_is_finite(table: list[list[int]]) -> None:
    result = evaluate_categorical(config(), observations(table))
    assert result.table == table
    for estimate in result.estimates:
        assert all(
            value is None or math.isfinite(value)
            for value in (estimate.value, estimate.low, estimate.high)
        )
    assert any(e.note for e in result.estimates)
    assert "Infinity" not in result.model_dump_json()


def test_empty_margins_reject_comparison_but_diagnostic_denominators_are_reported() -> (
    None
):
    with pytest.raises(ValueError, match="nonempty"):
        evaluate_categorical(config(), observations([[0, 5], [0, 5]]))
    result = evaluate_categorical(
        config("diagnostic_accuracy", groups=[], design=None, reference="reference"),
        observations([[0, 5], [0, 5]], True),
    )
    sensitivity = result.estimates[0]
    assert sensitivity.value is None and "denominator is zero" in sensitivity.note


@pytest.mark.parametrize(
    "overrides",
    [
        {"groups": ["a", "a"]},
        {"design": None},
        {"reference": "other"},
        {"alpha": 0},
        {"alpha": 1},
        {"alpha": float("nan")},
        {
            "method": "diagnostic_accuracy",
            "reference": "disease",
            "groups": [],
            "design": None,
        },
    ],
)
def test_invalid_configuration_fails(overrides: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        config(**overrides)


def test_diagnostic_excludes_entire_incomplete_pair_and_respects_alpha() -> None:
    rows = observations([[8, 1], [2, 9]], True)
    rows.append(
        CategoricalObservation(
            "missing", "exposed", {"disease": "positive", "reference": "missing"}
        )
    )
    result = evaluate_categorical(
        config(
            "diagnostic_accuracy",
            groups=[],
            design=None,
            reference="reference",
            missing="complete_case",
            alpha=0.1,
        ),
        rows,
    )
    assert result.table == [[8, 1], [2, 9]]
    assert result.excluded == 1 and result.observations == 20
    assert result.estimates[0].low == pytest.approx(
        stats.binomtest(8, 10).proportion_ci(confidence_level=0.9, method="wilson").low
    )
    with pytest.raises(ValueError, match="at least two"):
        evaluate_categorical(config(), observations([[1, 0], [0, 0]]))
