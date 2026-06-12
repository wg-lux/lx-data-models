from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


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
    subcategories: dict[str, object] = Field(default_factory=dict)
    numerical_descriptors: dict[str, object] = Field(default_factory=dict)


class PatientFindingClassificationCore(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    patient_finding_id: int
    finding_name: str
    classification_name: str
    classification_choice_name: str
    is_active: bool = True
    subcategories: dict[str, object] = Field(default_factory=dict)
    numerical_descriptors: dict[str, object] = Field(default_factory=dict)


__all__ = [
    "FindingClassificationTypeCore",
    "FindingClassificationCore",
    "FindingClassificationChoiceCore",
    "PatientFindingClassificationCore",
]
