import math

import pytest
from pydantic import ValidationError
from scipy import stats

from lx_dtypes.models.contracts.study_analysis import StudyInference
from lx_dtypes.stats.study_inference import NumericObservation, evaluate_inference


def rows() -> list[NumericObservation]:
    return [
        NumericObservation(str(i), "a" if i < 3 else "b", {"y": y, "x": x, "z": z})
        for i, (y, x, z) in enumerate(
            zip(
                [2.0, 3.0, 7.0, 4.0, 8.0, 11.0],
                [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
                [2.0, 0.0, 1.0, 3.0, 0.0, 2.0],
                strict=True,
            )
        )
    ]


@pytest.mark.parametrize("method", ["welch_t_test", "paired_t_test"])
@pytest.mark.parametrize("alpha", [0.05, 0.1])
def test_t_tests_match_scipy(method: str, alpha: float) -> None:
    config = StudyInference.model_validate(
        dict(
            name="comparison",
            method=method,
            outcome="y",
            alpha=alpha,
            **(
                {"groups": ["a", "b"]}
                if method == "welch_t_test"
                else {"paired_variable": "x"}
            ),
        )
    )
    result = evaluate_inference(config, rows())
    reference = (
        stats.ttest_ind([2, 3, 7], [4, 8, 11], equal_var=False)
        if method == "welch_t_test"
        else stats.ttest_rel([2, 3, 7, 4, 8, 11], [1, 2, 3, 4, 5, 6])
    )
    interval = reference.confidence_interval(1 - alpha)
    if method == "welch_t_test":
        assert [(entry.group, entry.count) for entry in result.group_counts] == [
            ("a", 3),
            ("b", 3),
        ]
    estimate = result.estimates[0]
    assert estimate.statistic == pytest.approx(reference.statistic)
    assert estimate.p_value == pytest.approx(reference.pvalue)
    assert result.degrees_of_freedom == pytest.approx(reference.df)
    assert estimate.confidence_low == pytest.approx(interval.low)
    assert estimate.confidence_high == pytest.approx(interval.high)


def test_multiple_regression_known_orthogonal_solution() -> None:
    observations = [
        NumericObservation(
            str(i), "a", {"x": x, "z": z, "y": 3 + 2 * x - 0.5 * z + error}
        )
        for i, (x, z, error) in enumerate(
            zip(
                [-2.0, -1.0, 0.0, 0.0, 1.0, 2.0],
                [1.0, -1.0, 0.0, 0.0, -1.0, 1.0],
                [0.0, 0.0, 1.0, -1.0, 0.0, 0.0],
                strict=True,
            )
        )
    ]
    config = StudyInference(
        name="regression",
        method="linear_regression",
        outcome="y",
        predictors=["x", "z"],
    )
    result = evaluate_inference(config, observations)
    assert [e.estimate for e in result.estimates] == pytest.approx([3, 2, -0.5])
    assert [e.standard_error for e in result.estimates] == pytest.approx(
        [1 / 3, math.sqrt(1 / 15), math.sqrt(1 / 6)]
    )
    assert result.degrees_of_freedom == 3
    assert result.r_squared == pytest.approx(41 / 43)
    assert result.estimates[1].p_value == pytest.approx(
        2 * stats.t.sf(math.sqrt(60), 3)
    )


def test_complete_case_keeps_pairs_together_and_counts_exclusions() -> None:
    observations = rows()
    observations[0].values["x"] = None
    config = StudyInference(
        name="paired", method="paired_t_test", outcome="y", paired_variable="x"
    )
    with pytest.raises(ValueError, match="missing inference"):
        evaluate_inference(config, observations)
    result = evaluate_inference(
        config.model_copy(update={"missing": "complete_case"}), observations
    )
    assert result.observations == 5
    assert result.missing_observations == 1
    assert result.estimates[0].statistic == pytest.approx(
        stats.ttest_rel([3, 7, 4, 8, 11], [2, 3, 4, 5, 6]).statistic
    )


@pytest.mark.parametrize(
    "failure", ["duplicate", "infinite", "nan", "constant", "rank", "small"]
)
def test_invalid_samples_fail(failure: str) -> None:
    observations = rows()
    config = StudyInference(
        name="regression",
        method="linear_regression",
        outcome="y",
        predictors=["x", "z"],
    )
    if failure == "duplicate":
        observations.append(observations[0])
    elif failure in {"infinite", "nan"}:
        observations[0].values["y"] = float("inf" if failure == "infinite" else "nan")
    elif failure == "small":
        observations = observations[:2]
    else:
        for row in observations:
            row.values["y" if failure == "constant" else "z"] = 1.0
    with pytest.raises(ValueError):
        evaluate_inference(config, observations)


@pytest.mark.parametrize(
    "payload",
    [
        {"method": "welch_t_test", "groups": ["a", "a"]},
        {"method": "paired_t_test", "paired_variable": "y"},
        {"method": "linear_regression", "predictors": ["y"]},
        {"method": "linear_regression", "predictors": ["x", "x"]},
        {"method": "linear_regression", "predictors": ["x"], "alpha": 0.0},
        {"method": "linear_regression", "predictors": ["x"], "missing": "impute"},
    ],
)
def test_invalid_configuration(payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        StudyInference.model_validate({"name": "invalid", "outcome": "y", **payload})
