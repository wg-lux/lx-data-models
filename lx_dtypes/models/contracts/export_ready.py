from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TypedDict

from pydantic import BaseModel, ConfigDict, field_validator

from lx_dtypes.models.contracts.json_types import JsonValue


class VideoReadyForExportData(TypedDict):
    center_key: str | None
    processed_file_sha256: str | None


class VideoReadyForExportPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    center_key: str | None = None
    processed_file_sha256: str | None = None

    @field_validator("center_key", "processed_file_sha256", mode="before")
    @classmethod
    def blank_to_none(cls, value: str | float | bool | None) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            return value.strip() or None
        converted = str(value).strip()
        return converted or None


@dataclass(frozen=True, slots=True)
class ReadyForExportResult:
    video_id: int
    ready_for_export: bool
    ready_for_export_at: str | None
    ready_for_export_by: str
    processed_file_sha256: str

    def to_dict(self) -> dict[str, JsonValue | None]:
        return {
            "video_id": self.video_id,
            "ready_for_export": self.ready_for_export,
            "ready_for_export_at": self.ready_for_export_at,
            "ready_for_export_by": self.ready_for_export_by,
            "processed_file_sha256": self.processed_file_sha256,
        }


def validate_video_ready_for_export_payload(
    payload: Mapping[str, JsonValue],
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
    "ReadyForExportResult",
    "VideoReadyForExportData",
    "VideoReadyForExportPayload",
    "dump_video_ready_for_export_payload",
    "validate_video_ready_for_export_payload",
]
