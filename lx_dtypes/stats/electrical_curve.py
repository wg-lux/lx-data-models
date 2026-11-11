"""Extract HF application curves and compare them with earlier curves.

Both functions are pure and deterministic. They fail loudly on ambiguous input
and never interpolate, zero-fill or carry measurement values forward.
"""

from __future__ import annotations

import math
from datetime import datetime
from fractions import Fraction

import numpy as np
from numpy.typing import NDArray

from lx_dtypes.models.contracts.electrical_curve import (
    ElectricalApplicationCurve,
    ElectricalApplicationSection,
    ElectricalApplicationSectionStatus,
    ElectricalCurveRegressionResult,
)
from lx_dtypes.models.contracts.electrosurgical_measurements import (
    ElectrosurgicalChannel,
    ElectrosurgicalMeasurementSeries,
    ElectrosurgicalQuantity,
)
from lx_dtypes.models.contracts.knowledge_base import KnowledgeBaseIdentity
from lx_dtypes.models.knowledge_base.electrical_curve_profile import (
    ElectricalCurveProfile,
)
from lx_dtypes.models.ledger.p_electrical_application import (
    PElectricalApplication,
    PElectricalCurveComparison,
)

FloatMatrix = NDArray[np.float64]


class ElectricalCurveError(ValueError):
    """Curves cannot be extracted or compared without violating an invariant."""


def _single_channel(
    series: ElectrosurgicalMeasurementSeries, quantity: ElectrosurgicalQuantity
) -> ElectrosurgicalChannel:
    matches = [channel for channel in series.channels if channel.quantity == quantity]
    if len(matches) != 1:
        raise ElectricalCurveError(
            f"Series requires exactly one {quantity} channel, found {len(matches)}"
        )
    return matches[0]


def _activation_runs(activation: list[float]) -> list[tuple[int, int]]:
    runs: list[tuple[int, int]] = []
    start: int | None = None
    for index, value in enumerate(activation):
        if value == 1.0 and start is None:
            start = index
        elif value == 0.0 and start is not None:
            runs.append((start, index))
            start = None
    if start is not None:
        runs.append((start, len(activation)))
    return runs


def extract_application_sections(
    series: ElectrosurgicalMeasurementSeries, profile: ElectricalCurveProfile
) -> list[ElectricalApplicationSection]:
    """Return every activation run with a status; only complete runs carry curves.

    A run touching the first or last sample is ``truncated`` because its true
    start or end was not recorded. Bin ``k`` of a run from ``start`` to ``end``
    (inclusive ticks) holds samples with ``floor((t - start) * bins / (end -
    start)) == k``; the final sample belongs to the last bin.
    """
    ticks = series.timestamps.presentation_timestamps
    base = Fraction(series.timestamps.time_base_num, series.timestamps.time_base_den)
    activation = _single_channel(series, "activation").values
    channels = [_single_channel(series, q) for q in profile.curve_quantities]
    max_gap_ticks = profile.max_sample_gap_seconds / base
    bins = profile.phase_bins

    sections: list[ElectricalApplicationSection] = []
    for low, high in _activation_runs(activation):
        start, end = ticks[low], ticks[high - 1]
        duration = (end - start) * base
        status: ElectricalApplicationSectionStatus = "complete"
        if low == 0 or high == len(ticks):
            status = "truncated"
        elif any(
            ticks[index + 1] - ticks[index] > max_gap_ticks
            for index in range(low, high - 1)
        ):
            status = "sample_gap"
        elif duration < profile.min_duration_seconds:
            status = "too_short"
        elif duration > profile.max_duration_seconds:
            status = "too_long"

        curve: ElectricalApplicationCurve | None = None
        if status == "complete":
            members: list[list[int]] = [[] for _ in range(bins)]
            for index in range(low, high):
                members[
                    min(bins - 1, (ticks[index] - start) * bins // (end - start))
                ].append(index)
            if any(not member for member in members):
                status = "empty_bin"
            else:
                curve = ElectricalApplicationCurve(
                    quantities=list(profile.curve_quantities),
                    bin_values=[
                        [
                            math.fsum(channel.values[i] for i in member) / len(member)
                            for channel in channels
                        ]
                        for member in members
                    ],
                    bin_sample_counts=[len(member) for member in members],
                )
        sections.append(
            ElectricalApplicationSection(
                sample_start_index=low,
                sample_end_index=high,
                start_timestamp=start,
                end_timestamp=end,
                status=status,
                curve=curve,
            )
        )
    return sections


def build_electrical_application(
    series: ElectrosurgicalMeasurementSeries,
    section: ElectricalApplicationSection,
    profile: ElectricalCurveProfile,
    identity: KnowledgeBaseIdentity,
    *,
    patient_examination: str,
    started_at: datetime,
) -> PElectricalApplication:
    """Bind a complete section to its source, clock and exact profile identity."""
    if section.curve is None:
        raise ElectricalCurveError(f"A {section.status} section has no curve")
    timestamps = series.timestamps
    application = PElectricalApplication(
        patient_examination=patient_examination,
        electrical_curve_profile=profile.name,
        knowledge_base_module=identity.knowledge_base_module,
        knowledge_base_version=identity.knowledge_base_version,
        measurement_source_sha256=series.source_sha256,
        session_id=timestamps.session_id,
        clock_id=timestamps.clock_id,
        time_base_num=timestamps.time_base_num,
        time_base_den=timestamps.time_base_den,
        sample_start_index=section.sample_start_index,
        sample_end_index=section.sample_end_index,
        start_timestamp=section.start_timestamp,
        end_timestamp=section.end_timestamp,
        started_at=started_at,
        curve=section.curve,
    )
    application.validate_profile(profile, identity)
    return application


def _design(
    profile: ElectricalCurveProfile, curve: ElectricalApplicationCurve
) -> tuple[FloatMatrix, FloatMatrix]:
    bins = len(curve.bin_values)
    phase = [(index + 0.5) / bins for index in range(bins)]
    columns: list[list[float]] = [[1.0] * bins]
    columns += [
        [value**power for value in phase]
        for power in range(1, profile.phase_polynomial_degree + 1)
    ]
    columns += [curve.column(quantity) for quantity in profile.predictor_quantities]
    responses = [curve.column(quantity) for quantity in profile.response_quantities]
    return np.array(columns, dtype=np.float64).T, np.array(
        responses, dtype=np.float64
    ).T


def fit_and_score_curves(
    profile: ElectricalCurveProfile,
    section: ElectricalApplicationCurve,
    references: list[ElectricalApplicationCurve],
) -> ElectricalCurveRegressionResult:
    """Fit ``Y = X B`` on reference curves and score the section's residuals."""
    if len(references) < profile.min_reference_applications:
        raise ElectricalCurveError("Too few reference curves for this profile")
    for curve in (section, *references):
        profile.validate_curve(curve)
    designs = [_design(profile, curve) for curve in references]
    x = np.vstack([design for design, _ in designs])
    y = np.vstack([response for _, response in designs])
    rows, terms = x.shape
    responses = y.shape[1]
    if int(np.linalg.matrix_rank(x)) < terms:
        raise ElectricalCurveError(
            "Reference design is rank deficient; predictors are collinear or constant"
        )
    if rows - terms < responses:
        raise ElectricalCurveError("Too few reference rows to estimate covariance")
    coefficients = np.linalg.lstsq(x, y, rcond=None)[0]
    residuals = y - x @ coefficients
    covariance = residuals.T @ residuals / (rows - terms)
    try:
        np.linalg.cholesky(covariance)
    except np.linalg.LinAlgError as error:
        raise ElectricalCurveError(
            "Reference residual covariance is singular; responses are degenerate"
        ) from error

    r_squared: list[float | None] = []
    for column in range(responses):
        total = float(np.sum((y[:, column] - y[:, column].mean()) ** 2))
        error_sum = float(np.sum(residuals[:, column] ** 2))
        r_squared.append(None if total == 0.0 else 1.0 - error_sum / total)

    section_x, section_y = _design(profile, section)
    section_residuals = section_y - section_x @ coefficients
    solved = np.linalg.solve(covariance, section_residuals.T).T
    distances = [
        max(0.0, float(value)) for value in np.sum(section_residuals * solved, axis=1)
    ]
    mean_distance = math.fsum(distances) / len(distances)
    rmse = [
        float(math.sqrt(np.mean(section_residuals[:, column] ** 2)))
        for column in range(responses)
    ]
    threshold = profile.max_mean_mahalanobis_squared
    return ElectricalCurveRegressionResult(
        design_terms=profile.design_terms,
        response_quantities=list(profile.response_quantities),
        coefficients=[[float(v) for v in row] for row in coefficients],
        residual_covariance=[[float(v) for v in row] for row in covariance],
        reference_row_count=rows,
        reference_r_squared=r_squared,
        section_rmse=rmse,
        bin_mahalanobis_squared=distances,
        mean_mahalanobis_squared=mean_distance,
        threshold=threshold,
        verdict="deviates" if mean_distance > threshold else "within_reference",
    )


def compare_electrical_application(
    profile: ElectricalCurveProfile,
    identity: KnowledgeBaseIdentity,
    application: PElectricalApplication,
    references: list[PElectricalApplication],
) -> PElectricalCurveComparison:
    """Compare one application with strictly earlier applications of one profile."""
    for record in (application, *references):
        record.validate_profile(profile, identity)
    identifiers = [str(reference.uuid) for reference in references]
    if len(set(identifiers)) != len(identifiers):
        raise ElectricalCurveError("Reference applications must be unique")
    if str(application.uuid) in identifiers:
        raise ElectricalCurveError("An application cannot be its own reference")
    if any(reference.started_at >= application.started_at for reference in references):
        raise ElectricalCurveError("Reference applications must start strictly earlier")
    result = fit_and_score_curves(
        profile, application.curve, [reference.curve for reference in references]
    )
    return PElectricalCurveComparison(
        patient_examination=application.patient_examination,
        electrical_curve_profile=application.electrical_curve_profile,
        knowledge_base_module=application.knowledge_base_module,
        knowledge_base_version=application.knowledge_base_version,
        application=str(application.uuid),
        reference_applications=identifiers,
        result=result,
    )


__all__ = [
    "ElectricalCurveError",
    "build_electrical_application",
    "compare_electrical_application",
    "extract_application_sections",
    "fit_and_score_curves",
]
