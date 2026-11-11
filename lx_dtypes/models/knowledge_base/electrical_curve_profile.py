"""Versioned definition of electrosurgical application curves and their regression."""

from fractions import Fraction
from typing import Self, TypedDict

from pydantic import Field, model_validator

from lx_dtypes.models.base.app_base_model.ddict.KnowledgebaseBaseModelDataDict import (
    KnowledgebaseBaseModelDataDict,
)
from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.contracts.electrical_curve import (
    MAX_PHASE_BINS,
    ElectricalApplicationCurve,
)
from lx_dtypes.models.contracts.electrosurgical_measurements import (
    ElectrosurgicalQuantity,
)


class ElectricalCurveProfileDataDict(KnowledgebaseBaseModelDataDict):
    curve_quantities: list[ElectrosurgicalQuantity]
    response_quantities: list[ElectrosurgicalQuantity]
    predictor_quantities: list[ElectrosurgicalQuantity]
    phase_bins: int
    phase_polynomial_degree: int
    min_duration_num: int
    min_duration_den: int
    max_duration_num: int
    max_duration_den: int
    max_sample_gap_num: int
    max_sample_gap_den: int
    min_reference_applications: int
    max_mean_mahalanobis_squared: float


class ElectricalCurveProfile(KnowledgebaseBaseModel[ElectricalCurveProfileDataDict]):
    """How HF activations become comparable curves and how they are compared.

    Durations and gaps are rational seconds. Responses are explained by an
    intercept, phase powers ``phase**1 .. phase**degree`` and the predictor
    quantities. Every response and predictor must be a curve quantity.
    """

    name: str = Field(min_length=1, max_length=255)
    curve_quantities: list[ElectrosurgicalQuantity] = Field(min_length=1)
    response_quantities: list[ElectrosurgicalQuantity] = Field(min_length=1)
    predictor_quantities: list[ElectrosurgicalQuantity] = Field(default_factory=list)
    phase_bins: int = Field(ge=2, le=MAX_PHASE_BINS)
    phase_polynomial_degree: int = Field(default=2, ge=0, le=5)
    min_duration_num: int = Field(gt=0)
    min_duration_den: int = Field(gt=0)
    max_duration_num: int = Field(gt=0)
    max_duration_den: int = Field(gt=0)
    max_sample_gap_num: int = Field(gt=0)
    max_sample_gap_den: int = Field(gt=0)
    min_reference_applications: int = Field(default=3, ge=2)
    max_mean_mahalanobis_squared: float = Field(gt=0, allow_inf_nan=False)

    @property
    def min_duration_seconds(self) -> Fraction:
        return Fraction(self.min_duration_num, self.min_duration_den)

    @property
    def max_duration_seconds(self) -> Fraction:
        return Fraction(self.max_duration_num, self.max_duration_den)

    @property
    def max_sample_gap_seconds(self) -> Fraction:
        return Fraction(self.max_sample_gap_num, self.max_sample_gap_den)

    @property
    def design_terms(self) -> list[str]:
        phase = [
            f"phase^{power}" for power in range(1, self.phase_polynomial_degree + 1)
        ]
        return ["intercept", *phase, *self.predictor_quantities]

    @model_validator(mode="after")
    def validate_profile(self) -> Self:
        for label, quantities in (
            ("Curve", self.curve_quantities),
            ("Response", self.response_quantities),
            ("Predictor", self.predictor_quantities),
        ):
            if len(set(quantities)) != len(quantities):
                raise ValueError(f"{label} quantities must be unique")
        if "activation" in self.curve_quantities:
            raise ValueError("Activation defines sections and is not a curve quantity")
        curve = set(self.curve_quantities)
        if not set(self.response_quantities) <= curve or not (
            set(self.predictor_quantities) <= curve
        ):
            raise ValueError("Responses and predictors must be curve quantities")
        if set(self.response_quantities) & set(self.predictor_quantities):
            raise ValueError("A quantity cannot be both response and predictor")
        if self.max_duration_seconds < self.min_duration_seconds:
            raise ValueError("Maximum duration must not be below the minimum")
        if self.phase_bins <= len(self.design_terms):
            raise ValueError("Phase bins must exceed the number of design terms")
        return self

    def validate_curve(self, curve: ElectricalApplicationCurve) -> None:
        if curve.quantities != self.curve_quantities:
            raise ValueError("Curve quantities disagree with the profile order")
        if len(curve.bin_values) != self.phase_bins:
            raise ValueError("Curve phase bins disagree with the profile")

    @property
    def ddict_class(self) -> type[ElectricalCurveProfileDataDict]:
        return ElectricalCurveProfileDataDict


class KbElectricalCurveProfileLookupType(TypedDict):
    ElectricalCurveProfile: type[ElectricalCurveProfile]


__all__ = [
    "ElectricalCurveProfile",
    "ElectricalCurveProfileDataDict",
    "KbElectricalCurveProfileLookupType",
]
