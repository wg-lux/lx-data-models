"""Independent-patient 2x2 inference from explicit endpoint states."""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

import numpy as np
from scipy import stats
from scipy.stats.contingency import odds_ratio, relative_risk

from lx_dtypes.models.contracts.study_analysis import (
    PlotState,
    StudyCategorical,
    StudyCategoricalEstimate,
    StudyCategoricalResult,
)


@dataclass(frozen=True)
class CategoricalObservation:
    patient: str
    group: str
    states: dict[str, PlotState]


def _ratio(
    term: str,
    value: float,
    low: float,
    high: float,
    interval: Literal["conditional_exact", "katz_log"],
) -> StudyCategoricalEstimate:
    # JSON cannot encode infinity. Preserve the reason for every absent value.
    notes = []
    for label, number in (
        ("estimate", value),
        ("lower limit", low),
        ("upper limit", high),
    ):
        if math.isnan(number):
            notes.append(f"Undefined {label}")
        elif math.isinf(number):
            notes.append(f"Unbounded {label}")
    return StudyCategoricalEstimate(
        term=term,
        value=value if math.isfinite(value) else None,
        low=low if math.isfinite(low) else None,
        high=high if math.isfinite(high) else None,
        interval=interval,
        note="; ".join(notes),
    )


def _proportion(
    term: str, numerator: int, denominator: int, alpha: float
) -> StudyCategoricalEstimate:
    if denominator == 0:
        return StudyCategoricalEstimate(
            term=term,
            value=None,
            low=None,
            high=None,
            interval="wilson",
            note="Undefined: denominator is zero",
        )
    interval = stats.binomtest(numerator, denominator).proportion_ci(
        confidence_level=1 - alpha, method="wilson"
    )
    return StudyCategoricalEstimate(
        term=term,
        value=numerator / denominator,
        low=float(interval.low),
        high=float(interval.high),
        interval="wilson",
    )


def evaluate_categorical(
    config: StudyCategorical, observations: Sequence[CategoricalObservation]
) -> StudyCategoricalResult:
    config = StudyCategorical.model_validate(config.model_dump())
    selected = [
        row for row in observations if not config.groups or row.group in config.groups
    ]
    if len({row.patient for row in selected}) != len(selected):
        raise ValueError("categorical inference requires one analysis unit per patient")
    table = [[0, 0], [0, 0]]
    excluded = 0
    for row in selected:
        names = [config.endpoint] + ([config.reference] if config.reference else [])
        if any(name not in row.states for name in names):
            raise ValueError("categorical observation is missing a configured endpoint")
        if any(row.states[name] not in {"positive", "negative"} for name in names):
            excluded += 1
            continue
        outcome = 0 if row.states[config.endpoint] == "positive" else 1
        if config.reference:
            reference = 0 if row.states[config.reference] == "positive" else 1
            table[outcome][reference] += 1
        else:
            table[config.groups.index(row.group)][outcome] += 1
    if excluded and config.missing == "error":
        raise ValueError(
            "categorical endpoints are unknown, conflicting or ineligible; configure complete_case explicitly"
        )
    count = sum(map(sum, table))
    if count < 2:
        raise ValueError(
            "categorical inference requires at least two complete observations"
        )
    a, b = table[0]
    c, d = table[1]
    statistic: float | None = None
    p: float | None = None
    df: int | None = None
    if config.method == "diagnostic_accuracy":
        estimates = [
            _proportion(term, numerator, denominator, config.alpha)
            for term, numerator, denominator in (
                ("sensitivity", a, a + c),
                ("specificity", d, b + d),
                ("positive_predictive_value", a, a + b),
                ("negative_predictive_value", d, c + d),
                ("accuracy", a + d, count),
            )
        ]
        rows = [f"{config.endpoint}: positive", f"{config.endpoint}: negative"]
        columns = [f"{config.reference}: positive", f"{config.reference}: negative"]
    else:
        if min(a + b, c + d, a + c, b + d) == 0:
            raise ValueError(
                "categorical comparison requires nonempty group and outcome margins"
            )
        if config.method == "chi_square":
            chi = stats.chi2_contingency(table, correction=False)
            if float(np.min(chi.expected_freq)) < 5:
                raise ValueError(
                    "chi-square requires expected cell counts of at least five; configure fisher_exact for sparse tables"
                )
            statistic, p, df = float(chi.statistic), float(chi.pvalue), int(chi.dof)
        else:
            p = float(
                stats.fisher_exact(np.asarray(table), alternative="two-sided").pvalue
            )
        odds = odds_ratio(table, kind="conditional")
        bounds = odds.confidence_interval(confidence_level=1 - config.alpha)
        estimates = [
            _ratio(
                "odds_ratio",
                float(odds.statistic),
                float(bounds.low),
                float(bounds.high),
                "conditional_exact",
            )
        ]
        if config.design == "cohort":
            risk = relative_risk(a, a + b, c, c + d)
            bounds = risk.confidence_interval(confidence_level=1 - config.alpha)
            estimates.append(
                _ratio(
                    "risk_ratio",
                    float(risk.relative_risk),
                    float(bounds.low),
                    float(bounds.high),
                    "katz_log",
                )
            )
        rows, columns = config.groups, ["positive", "negative"]
    return StudyCategoricalResult(
        name=config.name,
        method=config.method,
        design=config.design,
        endpoint=config.endpoint,
        reference=config.reference,
        alpha=config.alpha,
        observations=count,
        excluded=excluded,
        rows=rows,
        columns=columns,
        table=table,
        statistic=statistic,
        p=p,
        df=df,
        estimates=estimates,
    )
