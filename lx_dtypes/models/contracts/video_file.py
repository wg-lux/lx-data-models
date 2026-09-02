# lx_dtypes/models/contracts/video_file.py
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from lx_dtypes.models.contracts.json_types import JsonNull, JsonValue

type FrameSourceMode = Literal["cache", "stream", "auto"]

type VideoFileMetaJsonValue = (
    JsonValue
    | JsonNull
    | list[VideoFileMetaJsonValue]
    | dict[str, VideoFileMetaJsonValue]
)

type VideoFileMetaJsonObject = dict[str, VideoFileMetaJsonValue]


class VideoFileIdentityPayload(BaseModel):
    """Stable identity/reference fields for a VideoFile-like object."""

    model_config = ConfigDict(extra="ignore", frozen=True, strict=True)

    pk: int | None = Field(default=None, ge=1)
    id: int | None = Field(default=None, ge=1)
    video_hash: str = Field(min_length=1)
    original_file_name: str | None = None

    @field_validator("id", mode="after")
    @classmethod
    def _id_or_pk(cls, value: int | None, info: ValidationInfo) -> int | None:
        return value


class VideoFileTechnicalMetadataPayload(BaseModel):
    """Technical scalar metadata from VideoFile / ffmpeg / import state."""

    model_config = ConfigDict(extra="ignore", frozen=True, strict=True)

    fps: float | None = Field(default=None, gt=0)
    duration: float | None = Field(default=None, ge=0)
    frame_count: int | None = Field(default=None, ge=0)
    width: int | None = Field(default=None, ge=1)
    height: int | None = Field(default=None, ge=1)
    suffix: str | None = None
    frame_dir: str = ""


class VideoFileStoragePayload(BaseModel):
    """Storage and stream path metadata that is safe to pass across boundaries."""

    model_config = ConfigDict(extra="ignore", frozen=True, strict=True)

    storage_mode: str = ""
    raw_streamable_relative_path: str = ""
    processed_streamable_relative_path: str = ""
    has_raw: bool = False
    is_processed: bool = False


class VideoFilePayload(
    VideoFileIdentityPayload,
    VideoFileTechnicalMetadataPayload,
    VideoFileStoragePayload,
):
    """Serializable VideoFile contract without Django ORM relations or methods."""

    model_config = ConfigDict(extra="ignore", frozen=True, strict=True)

    uploaded_at: datetime | None = None
    date_created: datetime | None = None
    date_modified: datetime | None = None
    meta: VideoFileMetaJsonObject | None = None


__all__ = [
    "FrameSourceMode",
    "VideoFileIdentityPayload",
    "VideoFileMetaJsonObject",
    "VideoFileMetaJsonValue",
    "VideoFilePayload",
    "VideoFileStoragePayload",
    "VideoFileTechnicalMetadataPayload",
]
