from __future__ import annotations

from pathlib import Path
from collections.abc import Callable, Mapping, Sequence
from typing import TypeAlias, cast

from pydantic import BaseModel, ConfigDict, Field, RootModel, field_validator

JsonPath: TypeAlias = str
ActivationCallable: TypeAlias = Callable[[float], float]


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
    if isinstance(value, (int,)):
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
    axes: list[int] = Field(
        default_factory=lambda: [2, 0, 1], min_length=3, max_length=3
    )
    batchsize: int = Field(ge=1)
    num_workers: int = Field(ge=0)
    activation: ActivationCallable | None = None
    labels: list[str]

    @field_validator("mean", "std", mode="before")
    @classmethod
    def _normalize_float_triplet(
        cls,
        value: Sequence[object],
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
    def _normalize_axes(cls, value: Sequence[object]) -> list[int]:
        if isinstance(value, (list, tuple)) and len(value) == 3:
            return [
                _coerce_int(value[0]),
                _coerce_int(value[1]),
                _coerce_int(value[2]),
            ]
        raise ValueError("axes must contain exactly three integer values")


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


class VideoSegmentsPayload(RootModel[dict[str, list[tuple[int, int]]]]):
    model_config = ConfigDict(frozen=True, strict=True)

    @field_validator("root", mode="before")
    @classmethod
    def _normalize_root(
        cls, value: Mapping[str, list[tuple[object, object]]] | Mapping[object, object]
    ) -> dict[str, list[tuple[int, int]]]:
        if not isinstance(value, Mapping):
            raise ValueError("Video sequences payload must be a JSON object.")

        normalized: dict[str, list[tuple[int, int]]] = {}
        for label, raw_sequences in cast(Mapping[object, object], value).items():
            if not isinstance(label, str) or raw_sequences is None:
                continue
            if not isinstance(raw_sequences, list):
                raise ValueError(
                    f"Sequences for label '{label}' must be a list of pairs."
                )
            converted: list[tuple[int, int]] = []
            for item in raw_sequences:
                if not isinstance(item, (list, tuple)) or len(item) != 2:
                    raise ValueError(
                        f"Invalid sequence entry for label '{label}': {item!r}"
                    )
                if not isinstance(item[0], int) or not isinstance(item[1], int):
                    raise ValueError(
                        f"Sequence coordinates must be int for label '{label}': {item!r}"
                    )
                converted.append((int(item[0]), int(item[1])))
            normalized[label] = converted

        return normalized

    def as_dict(self) -> dict[str, list[tuple[int, int]]]:
        return cast(dict[str, list[tuple[int, int]]], self.model_dump(mode="python"))


def to_json_path(path: str | Path) -> JsonPath:
    return str(path)


__all__ = [
    "ActivationCallable",
    "AiPredictionConfigPayload",
    "AiPredictionPostProcessPayload",
    "AiPredictionResultPayload",
    "VideoSegmentsPayload",
    "AiPredictionSequencePayload",
    "AiPredictionSerializablePostProcessPayload",
    "JsonPath",
    "to_json_path",
]
