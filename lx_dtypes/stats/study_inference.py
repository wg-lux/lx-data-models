"""Local two-sided inference on validated, independent patient observations."""

import math
import sys
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from scipy import stats

from lx_dtypes.models.contracts.study_analysis import (
    StudyEstimate,
    StudyGroupCount,
    StudyInference,
    StudyInferenceResult,
    StudyNumericVariable,
    StudyRole,
)
from lx_dtypes.models.ledger.p_finding.Pydantic import PFinding

from .study_linkage import latest_study_choices


@dataclass(frozen=True)
class NumericObservation:
    patient: str
    group: str
    values: dict[str, float | None]


def numeric_values(
    variables: Sequence[StudyNumericVariable], findings: dict[StudyRole, PFinding]
) -> dict[str, float | None]:
    values: dict[str, float | None] = {}
    for variable in variables:
        finding = findings.get(variable.role)
        choices = (
            []
            if finding is None
            else [
                choice
                for choice in latest_study_choices(finding)
                if choice.classification == variable.classification
            ]
        )
        descriptors = (
            []
            if len(choices) != 1
            else [
                item
                for item in choices[0].patient_finding_classification_choice_descriptors
                if item.classification_choice_descriptor == variable.descriptor
            ]
        )
        value = descriptors[0].descriptor_value if len(descriptors) == 1 else None
        if value is not None and (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise ValueError("inference requires finite numeric observations")
        values[variable.name] = float(value) if value is not None else None
    return values


def _estimate(
    term: str, value: float, error: float, df: float, alpha: float
) -> StudyEstimate:
    if not math.isfinite(error) or error <= 0:
        raise ValueError("inference requires positive finite sampling variance")
    statistic = value / error
    critical = float(stats.t.ppf(1 - alpha / 2, df))
    return StudyEstimate(
        term=term,
        estimate=value,
        standard_error=error,
        statistic=statistic,
        p_value=float(2 * stats.t.sf(abs(statistic), df)),
        confidence_low=value - critical * error,
        confidence_high=value + critical * error,
    )


def evaluate_inference(
    config: StudyInference, observations: Sequence[NumericObservation]
) -> StudyInferenceResult:
    """Complete cases are explicit; no imputation or automatic patient aggregation."""
    config = StudyInference.model_validate(config.model_dump())
    selected = [
        row for row in observations if not config.groups or row.group in config.groups
    ]
    if len({row.patient for row in selected}) != len(selected):
        raise ValueError("inference requires one analysis unit per patient")
    names = [config.outcome, *config.predictors]
    if config.paired_variable:
        names.append(config.paired_variable)
    complete: list[NumericObservation] = []
    for row in selected:
        if any(name not in row.values for name in names):
            raise ValueError("inference observation is missing a configured variable")
        values = [row.values[name] for name in names]
        if any(
            value is not None and (isinstance(value, bool) or not math.isfinite(value))
            for value in values
        ):
            raise ValueError("inference requires finite numeric observations")
        if all(value is not None for value in values):
            complete.append(row)
    missing = len(selected) - len(complete)
    if missing and config.missing == "error":
        raise ValueError(
            "missing inference observations; configure complete_case explicitly to exclude them"
        )
    data = np.array(
        [[row.values[name] for name in names] for row in complete], dtype=float
    )
    if len(complete) < 2:
        raise ValueError("inference requires at least two complete observations")
    counts: dict[str, int] = {}
    r_squared: float | None = None
    if config.method == "linear_regression":
        x = np.column_stack((np.ones(len(complete)), data[:, 1:]))
        y = data[:, 0]
        beta, _, rank, _ = np.linalg.lstsq(x, y, rcond=None)
        df = float(len(y) - x.shape[1])
        if rank != x.shape[1] or df <= 0:
            raise ValueError(
                "regression requires full rank and positive residual degrees of freedom"
            )
        residual = y - x @ beta
        rss = float(residual @ residual)
        total = float(np.sum((y - y.mean()) ** 2))
        if total <= 0 or rss <= sys.float_info.epsilon * total:
            raise ValueError(
                "regression requires nonconstant outcomes and nonzero residual variance"
            )
        inverse = np.linalg.pinv(x)
        errors = np.sqrt(np.sum(inverse**2, axis=1) * rss / df)
        estimates = [
            _estimate(term, float(value), float(error), df, config.alpha)
            for term, value, error in zip(
                ["intercept", *config.predictors], beta, errors, strict=True
            )
        ]
        r_squared = 1 - rss / total
    else:
        if config.method == "paired_t_test":
            differences = data[:, 0] - data[:, 1]
            value = float(differences.mean())
            variance = float(differences.var(ddof=1)) / len(differences)
            df = float(len(differences) - 1)
        else:
            samples = [
                np.array(
                    [
                        row.values[config.outcome]
                        for row in complete
                        if row.group == group
                    ],
                    dtype=float,
                )
                for group in config.groups
            ]
            counts = {
                group: len(sample)
                for group, sample in zip(config.groups, samples, strict=True)
            }
            if any(len(sample) < 2 for sample in samples):
                raise ValueError(
                    "Welch test requires at least two complete observations in each group"
                )
            first, second = samples
            a, b = (
                float(first.var(ddof=1)) / len(first),
                float(second.var(ddof=1)) / len(second),
            )
            variance = a + b
            if variance <= 0:
                raise ValueError("inference requires positive finite sampling variance")
            df = variance**2 / (a**2 / (len(first) - 1) + b**2 / (len(second) - 1))
            value = float(first.mean() - second.mean())
        estimates = [
            _estimate("mean_difference", value, math.sqrt(variance), df, config.alpha)
        ]
    return StudyInferenceResult(
        name=config.name,
        method=config.method,
        alpha=config.alpha,
        observations=len(complete),
        missing_observations=missing,
        group_counts=[
            StudyGroupCount(group=group, count=count) for group, count in counts.items()
        ],
        degrees_of_freedom=df,
        r_squared=r_squared,
        estimates=estimates,
    )
