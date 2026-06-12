from __future__ import annotations

from pathlib import Path
from typing import TypeAlias, cast

from pydantic import BaseModel, ConfigDict, Field

JsonPath: TypeAlias = str


class AiPredictionConfigPayload(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        arbitrary_types_allowed=True,
    )

    mean: tuple[float, float, float]
    std: tuple[float, float, float]
    size_x: int = Field(ge=1)
    size_y: int = Field(ge=1)
    axes: list[int]
    batchsize: int = Field(ge=1)
    num_workers: int = Field(ge=0)
    activation: object | None = None
    labels: list[str]


class AiPredictionResultPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    labels: list[str]
    paths: list[JsonPath]
    predictions: list[list[float]]


class AiPredictionSequencePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    start: int
    stop: int


class AiPredictionPostProcessPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    predictions: dict[str, list[float]]
    smooth_predictions: dict[str, list[float]]
    binary_predictions: dict[str, list[bool]]
    raw_sequences: dict[str, list[AiPredictionSequencePayload]]
    filtered_sequences: dict[str, list[AiPredictionSequencePayload]]


class AiPredictionSerializablePostProcessPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    predictions: dict[str, list[float]]
    smooth_predictions: dict[str, list[float]]
    binary_predictions: dict[str, list[bool]]
    raw_sequences: dict[str, dict[str, list[int]]]
    filtered_sequences: dict[str, dict[str, list[int]]]


def to_json_path(path: str | Path) -> JsonPath:
    return cast(JsonPath, str(path))


__all__ = [
    "AiPredictionConfigPayload",
    "AiPredictionPostProcessPayload",
    "AiPredictionResultPayload",
    "AiPredictionSequencePayload",
    "AiPredictionSerializablePostProcessPayload",
    "JsonPath",
    "to_json_path",
]
