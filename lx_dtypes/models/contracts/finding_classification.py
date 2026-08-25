from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from lx_dtypes.models.contracts.json_types import JsonValue


class FindingClassificationTypeCore(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    name: str
    description: str = ""


class FindingClassificationCore(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    name: str
    description: str = ""


class FindingClassificationChoiceCore(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    name: str
    description: str = ""
    subcategories: dict[str, JsonValue] = Field(default_factory=dict)
    numerical_descriptors: dict[str, JsonValue] = Field(default_factory=dict)


class PatientFindingClassificationCore(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    patient_finding_id: int
    finding_name: str
    classification_name: str
    classification_choice_name: str
    is_active: bool = True
    subcategories: dict[str, JsonValue] = Field(default_factory=dict)
    numerical_descriptors: dict[str, JsonValue] = Field(default_factory=dict)


__all__ = [
    "FindingClassificationChoiceCore",
    "FindingClassificationCore",
    "FindingClassificationTypeCore",
    "PatientFindingClassificationCore",
]
