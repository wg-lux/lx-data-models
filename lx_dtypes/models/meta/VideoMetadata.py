from __future__ import annotations

from enum import Enum
from typing import Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field


class VideoMetadataAnonymizationState(str, Enum):
    """Transport-safe anonymization states for video metadata responses."""

    NOT_STARTED = "not_started"
    EXTRACTING_FRAMES = "extracting_frames"
    PROCESSING_ANONYMIZING = "processing_anonymization"
    DONE_PROCESSING_ANONYMIZATION = "done_processing_anonymization"
    VALIDATED = "validated"
    FAILED = "failed"
    STARTED = "started"
    ANONYMIZED = "anonymized"


VideoMetadataStatus: TypeAlias = VideoMetadataAnonymizationState | Literal["BLANK"]


class VideoFpsDetailsPayload(BaseModel):
    """Validated details payload for an FPS lookup failure."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    video_id: int = Field(ge=1)
    reason: str = Field(min_length=1)


class VideoFpsErrorPayload(BaseModel):
    """Validated error payload for the video FPS endpoint."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    error: str = Field(min_length=1)
    details: VideoFpsDetailsPayload


class VideoFpsStatsPayload(BaseModel):
    """Validated success payload for the video FPS endpoint."""

    model_config = ConfigDict(extra="forbid")

    video_id: int = Field(ge=1)
    fps: float = Field(gt=0.0)


VideoFpsPayload: TypeAlias = VideoFpsStatsPayload | VideoFpsErrorPayload


class VideoMetadataStatsPayload(BaseModel):
    """Validated response payload for the video metadata statistics endpoint."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    id: int = Field(ge=1)
    original_file_name: str = Field(min_length=1)
    status: VideoMetadataStatus
    assigned_user: str
    anonymized: bool
    duration: float = Field(ge=0.0)
    fps: float = Field(gt=0.0)
    has_roi: bool
    outside_frame_count: int = Field(ge=0)
    center_name: str = Field(min_length=1)
    processor_name: str = Field(min_length=1)
    sensitive_frame_count: int | None = Field(default=None, ge=0)
    total_frames: int | None = Field(default=None, ge=0)
    sensitive_ratio: float | None = Field(default=None, ge=0.0, le=1.0)
    resolution: str = Field(min_length=1)


__all__ = [
    "VideoFpsDetailsPayload",
    "VideoFpsErrorPayload",
    "VideoFpsPayload",
    "VideoFpsStatsPayload",
    "VideoMetadataAnonymizationState",
    "VideoMetadataStatsPayload",
    "VideoMetadataStatus",
]
