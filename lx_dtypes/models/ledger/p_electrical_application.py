"""Electrosurgical application curves and their comparisons to earlier curves."""

from datetime import UTC, datetime
from fractions import Fraction
from typing import Literal, Self, TypedDict

from pydantic import AwareDatetime, Field, field_validator, model_validator

from lx_dtypes.models.base.app_base_model.ddict.LedgerBaseModelDataDict import (
    LedgerBaseModelDataDict,
)
from lx_dtypes.models.base.app_base_model.pydantic.LedgerBaseModel import (
    LedgerBaseModel,
)
from lx_dtypes.models.contracts.electrical_curve import (
    ELECTRICAL_CURVE_REGRESSION_ALGORITHM,
    ElectricalApplicationCurve,
    ElectricalCurveRegressionResult,
)
from lx_dtypes.models.contracts.json_types import JsonObject
from lx_dtypes.models.contracts.knowledge_base import KnowledgeBaseIdentity
from lx_dtypes.models.knowledge_base.electrical_curve_profile import (
    ElectricalCurveProfile,
)

_SHA256 = r"^[0-9a-f]{64}$"
_OPAQUE_ID = r"^[0-9a-f]{32}$"
_IDENTITY_PART = r"^[^@]+$"


def _validate_profile_identity(
    names: tuple[str, str, str],
    profile: ElectricalCurveProfile,
    identity: KnowledgeBaseIdentity,
) -> None:
    profile_name, module, version = names
    if profile_name != profile.name or (
        module != profile.kb_module_name
        or module != identity.knowledge_base_module
        or version != identity.knowledge_base_version
    ):
        raise ValueError(
            "Electrical observation must match its exact KB profile identity"
        )


class PElectricalApplicationDataDict(LedgerBaseModelDataDict):
    patient_examination: str
    electrical_curve_profile: str
    knowledge_base_module: str
    knowledge_base_version: str
    measurement_source_sha256: str
    session_id: str
    clock_id: str
    time_base_num: int
    time_base_den: int
    sample_start_index: int
    sample_end_index: int
    start_timestamp: int
    end_timestamp: int
    started_at: datetime
    curve: JsonObject


class PElectricalApplication(LedgerBaseModel[PElectricalApplicationDataDict]):
    """One complete HF activation section of one measurement source.

    ``started_at`` orders applications across examinations; derive it from a
    recorded electrosurgery-to-examination time offset, never from file times.
    """

    patient_examination: str = Field(min_length=1)
    electrical_curve_profile: str = Field(min_length=1)
    knowledge_base_module: str = Field(min_length=1, pattern=_IDENTITY_PART)
    knowledge_base_version: str = Field(min_length=1, pattern=_IDENTITY_PART)
    measurement_source_sha256: str = Field(pattern=_SHA256)
    session_id: str = Field(pattern=_OPAQUE_ID)
    clock_id: str = Field(pattern=_OPAQUE_ID)
    time_base_num: int = Field(gt=0)
    time_base_den: int = Field(gt=0)
    sample_start_index: int = Field(ge=0)
    sample_end_index: int = Field(gt=0)
    start_timestamp: int
    end_timestamp: int
    started_at: AwareDatetime
    curve: ElectricalApplicationCurve

    @field_validator("started_at")
    @classmethod
    def normalize_utc(cls, value: datetime) -> datetime:
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_range(self) -> Self:
        if self.sample_end_index <= self.sample_start_index:
            raise ValueError("Application sample range must not be empty")
        if self.end_timestamp <= self.start_timestamp:
            raise ValueError("Application end must follow its start")
        return self

    def validate_profile(
        self, profile: ElectricalCurveProfile, identity: KnowledgeBaseIdentity
    ) -> None:
        _validate_profile_identity(
            (
                self.electrical_curve_profile,
                self.knowledge_base_module,
                self.knowledge_base_version,
            ),
            profile,
            identity,
        )
        profile.validate_curve(self.curve)
        duration = (self.end_timestamp - self.start_timestamp) * Fraction(
            self.time_base_num, self.time_base_den
        )
        if (
            not profile.min_duration_seconds
            <= duration
            <= (profile.max_duration_seconds)
        ):
            raise ValueError("Application duration lies outside the profile limits")

    @property
    def ddict_class(self) -> type[PElectricalApplicationDataDict]:
        return PElectricalApplicationDataDict

    @classmethod
    def nested_fields(cls) -> list[str]:
        return []


class PElectricalCurveComparisonDataDict(LedgerBaseModelDataDict):
    patient_examination: str
    electrical_curve_profile: str
    knowledge_base_module: str
    knowledge_base_version: str
    algorithm: str
    application: str
    reference_applications: list[str]
    result: JsonObject


class PElectricalCurveComparison(LedgerBaseModel[PElectricalCurveComparisonDataDict]):
    """Regression comparison of one application with strictly earlier references.

    ``application`` and ``reference_applications`` are ledger UUIDs of
    ``PElectricalApplication`` records bound to the same profile identity.
    """

    patient_examination: str = Field(min_length=1)
    electrical_curve_profile: str = Field(min_length=1)
    knowledge_base_module: str = Field(min_length=1, pattern=_IDENTITY_PART)
    knowledge_base_version: str = Field(min_length=1, pattern=_IDENTITY_PART)
    algorithm: Literal["electrical_curve_mvr_v1"] = (
        ELECTRICAL_CURVE_REGRESSION_ALGORITHM
    )
    application: str = Field(min_length=1)
    reference_applications: list[str] = Field(min_length=2)
    result: ElectricalCurveRegressionResult

    @model_validator(mode="after")
    def validate_references(self) -> Self:
        if len(set(self.reference_applications)) != len(self.reference_applications):
            raise ValueError("Reference applications must be unique")
        if self.application in self.reference_applications:
            raise ValueError("An application cannot be its own reference")
        return self

    def validate_profile(
        self, profile: ElectricalCurveProfile, identity: KnowledgeBaseIdentity
    ) -> None:
        _validate_profile_identity(
            (
                self.electrical_curve_profile,
                self.knowledge_base_module,
                self.knowledge_base_version,
            ),
            profile,
            identity,
        )
        if (
            self.result.design_terms != profile.design_terms
            or self.result.response_quantities != profile.response_quantities
            or self.result.threshold != profile.max_mean_mahalanobis_squared
        ):
            raise ValueError("Comparison result disagrees with its profile")
        if len(self.reference_applications) < profile.min_reference_applications:
            raise ValueError(
                "Comparison has fewer references than the profile requires"
            )

    @property
    def ddict_class(self) -> type[PElectricalCurveComparisonDataDict]:
        return PElectricalCurveComparisonDataDict

    @classmethod
    def nested_fields(cls) -> list[str]:
        return []


class LPElectricalApplicationLookupType(TypedDict):
    PElectricalApplication: type[PElectricalApplication]
    PElectricalCurveComparison: type[PElectricalCurveComparison]


__all__ = [
    "LPElectricalApplicationLookupType",
    "PElectricalApplication",
    "PElectricalApplicationDataDict",
    "PElectricalCurveComparison",
    "PElectricalCurveComparisonDataDict",
]
