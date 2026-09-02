from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ModelMetaInferenceDatasetConfigData(TypedDict):
    mean: tuple[float, float, float]
    std: tuple[float, float, float]
    size_x: int
    size_y: int
    axes: tuple[int, int, int]


class ModelMetaConfigData(TypedDict):
    name: str
    version: str
    model_name: str
    labelset_name: str
    activation: str
    weights_path: str
    mean: str
    std: str
    size_x: int
    size_y: int
    axes: str
    batchsize: int
    num_workers: int
    description: str


def _coerce_float(value: object) -> float:
    if isinstance(value, bool):
        return float(int(value))
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            raise ValueError("value cannot be blank")
        return float(stripped)
    raise ValueError("value must be numeric")


def _coerce_int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float):
        if not value.is_integer():
            raise ValueError("value must be an integer")
        return int(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            raise ValueError("value cannot be blank")
        return int(float(stripped)) if "." in stripped else int(stripped)
    raise ValueError("value must be an integer")


class ModelMetaInferenceDatasetConfigPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    mean: tuple[float, float, float]
    std: tuple[float, float, float]
    size_x: int = Field(ge=1)
    size_y: int = Field(ge=1)
    axes: tuple[int, int, int]

    @field_validator("mean", "std", mode="before")
    @classmethod
    def _normalize_float_triplet(
        cls,
        value: list[object] | tuple[object, ...],
    ) -> tuple[float, float, float]:
        if isinstance(value, (list, tuple)) and len(value) == 3:
            return (
                _coerce_float(value[0]),
                _coerce_float(value[1]),
                _coerce_float(value[2]),
            )
        raise ValueError("mean/std must contain exactly three numeric values")

    @field_validator("axes", mode="before")
    @classmethod
    def _normalize_axes(
        cls,
        value: list[object] | tuple[object, ...],
    ) -> tuple[int, int, int]:
        if isinstance(value, (list, tuple)) and len(value) == 3:
            return (
                _coerce_int(value[0]),
                _coerce_int(value[1]),
                _coerce_int(value[2]),
            )
        raise ValueError("axes must contain exactly three integer values")


class ModelMetaConfigPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    labelset_name: str = Field(min_length=1)
    activation: str = Field(min_length=1)
    weights_path: str = ""
    mean: str = Field(min_length=1)
    std: str = Field(min_length=1)
    size_x: int = Field(ge=1)
    size_y: int = Field(ge=1)
    axes: str = Field(min_length=1)
    batchsize: int = Field(ge=1)
    num_workers: int = Field(ge=0)
    description: str = ""


__all__ = [
    "ModelMetaConfigData",
    "ModelMetaConfigPayload",
    "ModelMetaInferenceDatasetConfigData",
    "ModelMetaInferenceDatasetConfigPayload",
]
