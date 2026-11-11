from __future__ import annotations

from pydantic import Field

from lx_dtypes.models.contracts.json_types import JsonValue
from lx_dtypes.models.model import FrozenContractModel


class ExaminationIndicationCore(FrozenContractModel):
    name: str
    description: str | None = None


class ExaminationIndicationClassificationCore(FrozenContractModel):
    name: str
    description: str | None = None


class ExaminationIndicationClassificationChoiceCore(FrozenContractModel):
    name: str
    subcategories: dict[str, JsonValue] = Field(default_factory=dict)
    numerical_descriptors: dict[str, JsonValue] = Field(default_factory=dict)


__all__ = [
    "ExaminationIndicationClassificationChoiceCore",
    "ExaminationIndicationClassificationCore",
    "ExaminationIndicationCore",
]
