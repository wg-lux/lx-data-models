from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SubcategoryDictContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    choices: list[str]
    default: str
    required: Literal[True]


class NumericalDescriptorContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    unit: str
    required: bool
    minimum: float | None = Field(alias="min")
    maximum: float | None = Field(alias="max")
    mean: float | None
    std: float | None
    default: float | None
    distribution: Literal["normal", "uniform"]


__all__ = ["NumericalDescriptorContract", "SubcategoryDictContract"]
