from __future__ import annotations

from pathlib import Path
from collections.abc import Callable, Mapping
from typing import TypeAlias, cast

from pydantic import BaseModel, ConfigDict, Field, RootModel, field_validator

JsonPath: TypeAlias = str
ActivationCallable: TypeAlias = Callable[[object], object]


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
        value: object,
    ) -> tuple[float, float, float]:
        if isinstance(value, (list, tuple)) and len(value) == 3:
            return (float(value[0]), float(value[1]), float(value[2]))
        raise ValueError("mean/std must contain exactly three numeric values")

    @field_validator("axes", mode="before")
    @classmethod
    def _normalize_axes(cls, value: object) -> list[int]:
        if isinstance(value, (list, tuple)) and len(value) == 3:
            return [int(value[0]), int(value[1]), int(value[2])]
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
    def _normalize_root(cls, value: object) -> dict[str, list[tuple[int, int]]]:
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
