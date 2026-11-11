"""Phase-binned electrosurgical application curves and regression comparisons.

An *application* is one maximal run of consecutive samples during which the HF
generator reports ``activation == 1``. Its duration is divided into equal-width
phase bins; each bin stores the unweighted mean of every curve channel. Phase
binning makes applications of different durations comparable without
interpolating or carrying values forward.
"""

from __future__ import annotations

import math
from typing import Final, Literal, Self

from pydantic import Field, model_validator

from lx_dtypes.models.model import FrozenContractModel

from .electrosurgical_measurements import ElectrosurgicalQuantity

ELECTRICAL_CURVE_REGRESSION_ALGORITHM: Final = "electrical_curve_mvr_v1"
MAX_PHASE_BINS: Final = 1000

ElectricalApplicationSectionStatus = Literal[
    "complete",
    "truncated",
    "too_short",
    "too_long",
    "sample_gap",
    "empty_bin",
]
ElectricalCurveVerdict = Literal["within_reference", "deviates"]


def _finite_matrix(rows: list[list[float]], label: str) -> None:
    if not all(math.isfinite(value) for row in rows for value in row):
        raise ValueError(f"{label} values must be finite")


class ElectricalApplicationCurve(FrozenContractModel):
    """Bin means in phase order; columns follow ``quantities``."""

    quantities: list[ElectrosurgicalQuantity] = Field(min_length=1)
    bin_values: list[list[float]] = Field(min_length=1, max_length=MAX_PHASE_BINS)
    bin_sample_counts: list[int] = Field(min_length=1, max_length=MAX_PHASE_BINS)

    @model_validator(mode="after")
    def validate_shape(self) -> Self:
        if len(set(self.quantities)) != len(self.quantities):
            raise ValueError("Curve quantities must be unique")
        if "activation" in self.quantities:
            raise ValueError("Activation defines the section and is not a curve value")
        if len(self.bin_sample_counts) != len(self.bin_values):
            raise ValueError("Every phase bin requires a sample count")
        if any(count < 1 for count in self.bin_sample_counts):
            raise ValueError("Every phase bin requires at least one sample")
        if any(len(row) != len(self.quantities) for row in self.bin_values):
            raise ValueError("Every phase bin requires one value per quantity")
        _finite_matrix(self.bin_values, "Curve")
        return self

    def column(self, quantity: ElectrosurgicalQuantity) -> list[float]:
        index = self.quantities.index(quantity)
        return [row[index] for row in self.bin_values]


class ElectricalApplicationSection(FrozenContractModel):
    """One activation run; a curve is present only for a complete section.

    Timestamps are native electrical ticks; ``sample_end_index`` is exclusive.
    """

    sample_start_index: int = Field(ge=0)
    sample_end_index: int = Field(gt=0)
    start_timestamp: int
    end_timestamp: int
    status: ElectricalApplicationSectionStatus
    curve: ElectricalApplicationCurve | None = None

    @model_validator(mode="after")
    def validate_section(self) -> Self:
        if self.sample_end_index <= self.sample_start_index:
            raise ValueError("Section sample range must not be empty")
        if self.end_timestamp < self.start_timestamp:
            raise ValueError("Section end must not precede its start")
        if (self.curve is not None) != (self.status == "complete"):
            raise ValueError("A curve is published exactly for complete sections")
        return self


class ElectricalCurveRegressionResult(FrozenContractModel):
    """Multivariate multiple regression fitted on reference curves only.

    The model is ``Y = X B + E``. Rows are phase bins of all reference
    applications; ``design_terms`` name the columns of ``X`` (intercept, phase
    powers, predictor quantities); columns of ``Y`` are ``response_quantities``.
    ``residual_covariance`` is ``E'E / (n - p)``. The compared section is scored
    by the mean over its bins of the squared Mahalanobis residual distance
    ``r' S^-1 r``, whose expectation is about the number of responses when the
    section behaves like the references.
    """

    algorithm: Literal["electrical_curve_mvr_v1"] = (
        ELECTRICAL_CURVE_REGRESSION_ALGORITHM
    )
    design_terms: list[str] = Field(min_length=1)
    response_quantities: list[ElectrosurgicalQuantity] = Field(min_length=1)
    coefficients: list[list[float]] = Field(min_length=1)
    residual_covariance: list[list[float]] = Field(min_length=1)
    reference_row_count: int = Field(gt=0)
    reference_r_squared: list[float | None]
    section_rmse: list[float]
    bin_mahalanobis_squared: list[float] = Field(min_length=1)
    mean_mahalanobis_squared: float = Field(ge=0, allow_inf_nan=False)
    threshold: float = Field(gt=0, allow_inf_nan=False)
    verdict: ElectricalCurveVerdict

    @model_validator(mode="after")
    def validate_result(self) -> Self:
        terms, responses = len(self.design_terms), len(self.response_quantities)
        if len(self.coefficients) != terms or any(
            len(row) != responses for row in self.coefficients
        ):
            raise ValueError("Coefficients must have one row per term and response")
        if len(self.residual_covariance) != responses or any(
            len(row) != responses for row in self.residual_covariance
        ):
            raise ValueError("Residual covariance must be square over the responses")
        if self.reference_row_count <= terms:
            raise ValueError("Reference rows must exceed the design terms")
        if (
            len(self.reference_r_squared) != responses
            or len(self.section_rmse) != responses
        ):
            raise ValueError("Fit statistics require one value per response")
        _finite_matrix(self.coefficients, "Coefficient")
        _finite_matrix(self.residual_covariance, "Covariance")
        _finite_matrix(
            [self.section_rmse, self.bin_mahalanobis_squared], "Residual statistic"
        )
        if any(
            value is not None and not math.isfinite(value)
            for value in self.reference_r_squared
        ):
            raise ValueError("R squared values must be finite when defined")
        if any(value < 0 for value in self.bin_mahalanobis_squared):
            raise ValueError("Squared distances must be nonnegative")
        expected_mean = math.fsum(self.bin_mahalanobis_squared) / len(
            self.bin_mahalanobis_squared
        )
        if not math.isclose(
            self.mean_mahalanobis_squared, expected_mean, rel_tol=1e-9, abs_tol=1e-12
        ):
            raise ValueError("Mean distance disagrees with the per-bin distances")
        expected = (
            "deviates"
            if self.mean_mahalanobis_squared > self.threshold
            else "within_reference"
        )
        if self.verdict != expected:
            raise ValueError("Verdict disagrees with the distance and threshold")
        return self


__all__ = [
    "ELECTRICAL_CURVE_REGRESSION_ALGORITHM",
    "MAX_PHASE_BINS",
    "ElectricalApplicationCurve",
    "ElectricalApplicationSection",
    "ElectricalApplicationSectionStatus",
    "ElectricalCurveRegressionResult",
    "ElectricalCurveVerdict",
]
