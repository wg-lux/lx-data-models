from __future__ import annotations

from typing import cast

from types import NoneType

from pydantic import BaseModel, ConfigDict, Field


type JsonNull = NoneType
type JsonScalar = str | int | float | bool
type JsonValue = JsonScalar | list[JsonValue] | dict[str, JsonValue]
type JsonObject = dict[str, JsonValue]
type JsonStringObject = dict[str, str]
type JsonNumericObject = dict[str, JsonScalar]


class VideoFrameCacheManifestLogPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    frame_dir: str
    file_count: int
    missing_frame_numbers: list[int] = Field(default_factory=list)
    extra_frame_numbers: list[int] = Field(default_factory=list)
    invalid_file_names: list[str] = Field(default_factory=list)
    duplicate_frame_numbers: list[int] = Field(default_factory=list)
    unexpected_file_names: list[str] = Field(default_factory=list)
    expected_count: int | None = None

    def to_log_payload(self) -> dict[str, JsonValue]:
        return cast(
            dict[str, JsonValue],
            self.model_dump(mode="python", exclude_none=True),
        )


class VideoFrameCacheValidationLogPayload(VideoFrameCacheManifestLogPayload):
    db_extracted_frame_count: int
    db_missing_frame_numbers: list[int] = Field(default_factory=list)
    db_extra_frame_numbers: list[int] = Field(default_factory=list)
    db_path_mismatch_frame_numbers: list[int] = Field(default_factory=list)
    db_missing_file_frame_numbers: list[int] = Field(default_factory=list)
    valid: bool = False


__all__ = [
    "JsonNull",
    "JsonObject",
    "JsonScalar",
    "JsonValue",
    "JsonNumericObject",
    "JsonStringObject",
    "VideoFrameCacheManifestLogPayload",
    "VideoFrameCacheValidationLogPayload",
]
