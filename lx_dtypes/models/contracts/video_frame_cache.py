from __future__ import annotations

from collections.abc import Mapping
from typing import cast

from pydantic import BaseModel, ConfigDict, Field

FrameCacheLogValue = str | int | float | bool | list[int] | list[str]
FrameCacheLogPayload = dict[str, FrameCacheLogValue]


class FrameCacheManifestLogPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    frame_dir: str
    file_count: int
    missing_frame_numbers: list[int] = Field(default_factory=list)
    extra_frame_numbers: list[int] = Field(default_factory=list)
    invalid_file_names: list[str] = Field(default_factory=list)
    duplicate_frame_numbers: list[int] = Field(default_factory=list)
    unexpected_file_names: list[str] = Field(default_factory=list)
    expected_count: int | None = None

    def as_log_payload(self) -> FrameCacheLogPayload:
        return cast(
            FrameCacheLogPayload,
            self.model_dump(mode="python", exclude_none=True),
        )


class FrameCacheValidationLogPayload(FrameCacheManifestLogPayload):
    db_extracted_frame_count: int = 0
    db_missing_frame_numbers: list[int] = Field(default_factory=list)
    db_extra_frame_numbers: list[int] = Field(default_factory=list)
    db_path_mismatch_frame_numbers: list[int] = Field(default_factory=list)
    db_missing_file_frame_numbers: list[int] = Field(default_factory=list)
    valid: bool = False


def parse_frame_cache_manifest_payload(
    payload: Mapping[str, object] | None,
) -> FrameCacheManifestLogPayload:
    return FrameCacheManifestLogPayload.model_validate(payload or {})


def parse_frame_cache_validation_payload(
    payload: Mapping[str, object] | None,
) -> FrameCacheValidationLogPayload:
    return FrameCacheValidationLogPayload.model_validate(payload or {})


__all__ = [
    "FrameCacheLogPayload",
    "FrameCacheLogValue",
    "FrameCacheManifestLogPayload",
    "FrameCacheValidationLogPayload",
    "parse_frame_cache_manifest_payload",
    "parse_frame_cache_validation_payload",
]
