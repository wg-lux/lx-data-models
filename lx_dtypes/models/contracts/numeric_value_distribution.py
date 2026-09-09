from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class NumericValueDistributionType(str, Enum):
    UNIFORM = "uniform"
    NORMAL = "normal"
    SKEWED_NORMAL = "skewed_normal"


class NumericValueDescriptorOperator(str, Enum):
    ADD = "+"
    SUBTRACT = "-"
    MULTIPLY = "x"
    DIVIDE = "/"


class NumericValueDistributionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    distribution_type: NumericValueDistributionType
    min_descriptor: str = Field(min_length=1)
    max_descriptor: str = Field(min_length=1)
    min_value: float | None = None
    max_value: float | None = None
    mean: float | None = None
    std_dev: float | None = None
    skewness: float | None = None


__all__ = [
    "NumericValueDescriptorOperator",
    "NumericValueDistributionPayload",
    "NumericValueDistributionType",
]
