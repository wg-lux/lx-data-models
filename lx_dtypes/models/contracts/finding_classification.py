from __future__ import annotations

from pydantic import Field

from lx_dtypes.models.contracts.json_types import JsonValue
from lx_dtypes.models.model import FrozenContractModel


class FindingClassificationTypeCore(FrozenContractModel):
    name: str
    description: str = ""


class FindingClassificationCore(FrozenContractModel):
    name: str
    description: str = ""


class FindingClassificationChoiceCore(FrozenContractModel):
    name: str
    description: str = ""
    subcategories: dict[str, JsonValue] = Field(default_factory=dict)
    numerical_descriptors: dict[str, JsonValue] = Field(default_factory=dict)


class PatientFindingClassificationCore(FrozenContractModel):
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
