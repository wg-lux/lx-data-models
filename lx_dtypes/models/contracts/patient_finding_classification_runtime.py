from __future__ import annotations

from math import isfinite
from typing import Literal, TypeAlias

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    field_validator,
    model_validator,
)
from lx_dtypes.models.contracts.json_types import JsonObject


class PatientFindingClassificationSubcategoryPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    required: bool = False
    choices: list[str] = Field(min_length=1)
    value: str | None = None

    @field_validator("choices")
    @classmethod
    def validate_choices(cls, value: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for choice in value:
            stripped = choice.strip()
            if not stripped:
                raise ValueError("choices must not contain blank values")
            if stripped in seen:
                raise ValueError("choices must not contain duplicate values")
            seen.add(stripped)
            normalized.append(stripped)
        return normalized

    @field_validator("value")
    @classmethod
    def validate_value_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("value must not be blank")
        return stripped

    @model_validator(mode="after")
    def validate_selected_value(
        self,
    ) -> PatientFindingClassificationSubcategoryPayload:
        if self.value is not None and self.value not in self.choices:
            raise ValueError("value must be one of choices")
        return self


class PatientFindingClassificationNumericalDescriptorPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    min: float = 0.0
    max: float = 1.0
    distribution: Literal["normal", "uniform"] = "normal"
    mean: float = 0.5
    std: float = Field(default=0.1, ge=0)
    value: float | None = None

    @field_validator("min", "max", "mean", "std", "value")
    @classmethod
    def validate_finite_number(cls, value: float | None) -> float | None:
        if value is not None and not isfinite(value):
            raise ValueError("numeric descriptor values must be finite")
        return value

    @model_validator(mode="after")
    def validate_numeric_bounds(
        self,
    ) -> PatientFindingClassificationNumericalDescriptorPayload:
        if self.min > self.max:
            raise ValueError("min must not exceed max")
        if self.mean < self.min or self.mean > self.max:
            raise ValueError("mean must be within min and max")
        if self.value is not None and (self.value < self.min or self.value > self.max):
            raise ValueError("value must be within min and max")
        return self


class PatientFindingClassificationSubcategoriesPayload(
    RootModel[dict[str, PatientFindingClassificationSubcategoryPayload]]
):
    model_config = ConfigDict(frozen=True, strict=True)


class PatientFindingClassificationNumericalDescriptorsPayload(
    RootModel[dict[str, PatientFindingClassificationNumericalDescriptorPayload]]
):
    model_config = ConfigDict(frozen=True, strict=True)


PatientFindingClassificationSubcategoriesData: TypeAlias = dict[str, JsonObject]
PatientFindingClassificationNumericalDescriptorsData: TypeAlias = dict[str, JsonObject]


__all__ = [
    "PatientFindingClassificationNumericalDescriptorPayload",
    "PatientFindingClassificationNumericalDescriptorsData",
    "PatientFindingClassificationNumericalDescriptorsPayload",
    "PatientFindingClassificationSubcategoryPayload",
    "PatientFindingClassificationSubcategoriesData",
    "PatientFindingClassificationSubcategoriesPayload",
]
