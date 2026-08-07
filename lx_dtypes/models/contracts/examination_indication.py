from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from lx_dtypes.models.contracts.json_types import JsonValue


class ExaminationIndicationCore(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    name: str
    description: str | None = None


class ExaminationIndicationClassificationCore(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    name: str
    description: str | None = None


class ExaminationIndicationClassificationChoiceCore(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    name: str
    subcategories: dict[str, JsonValue] = Field(default_factory=dict)
    numerical_descriptors: dict[str, JsonValue] = Field(default_factory=dict)


__all__ = [
    "ExaminationIndicationCore",
    "ExaminationIndicationClassificationCore",
    "ExaminationIndicationClassificationChoiceCore",
]
