from __future__ import annotations

from typing import Literal

from pydantic import Field

from lx_dtypes.models.model import FrozenContractModel


class SubcategoryDictContract(FrozenContractModel):
    choices: list[str]
    default: str
    required: Literal[True]


class NumericalDescriptorContract(FrozenContractModel):
    unit: str
    required: bool
    minimum: float | None = Field(alias="min")
    maximum: float | None = Field(alias="max")
    mean: float | None
    std: float | None
    default: float | None
    distribution: Literal["normal", "uniform"]


__all__ = ["NumericalDescriptorContract", "SubcategoryDictContract"]
