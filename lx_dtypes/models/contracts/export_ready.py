from __future__ import annotations

from collections.abc import Mapping
from typing import TypedDict

from pydantic import BaseModel, ConfigDict, field_validator


class VideoReadyForExportData(TypedDict):
    center_key: str | None
    processed_file_sha256: str | None


class VideoReadyForExportPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    center_key: str | None = None
    processed_file_sha256: str | None = None

    @field_validator("center_key", "processed_file_sha256", mode="before")
    @classmethod
    def blank_to_none(cls, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, str):
            return value.strip() or None
        return value


def validate_video_ready_for_export_payload(
    payload: Mapping[str, object],
) -> VideoReadyForExportPayload:
    return VideoReadyForExportPayload.model_validate(dict(payload))


def dump_video_ready_for_export_payload(
    payload: VideoReadyForExportPayload,
) -> VideoReadyForExportData:
    return {
        "center_key": payload.center_key,
        "processed_file_sha256": payload.processed_file_sha256,
    }


__all__ = [
    "VideoReadyForExportData",
    "VideoReadyForExportPayload",
    "dump_video_ready_for_export_payload",
    "validate_video_ready_for_export_payload",
]
