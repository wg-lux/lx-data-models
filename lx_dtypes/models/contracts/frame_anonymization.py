from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FrameVideoAnalysisResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    file_readable: bool = False
    has_video_stream: bool = False
    has_audio_stream: bool = False
    duration: float | None = None
    codec: str | None = None
    resolution: str | None = None
    frame_count: str | int | None = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class FrameStreamingCompatibilityResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    web_compatible: bool = False
    streaming_friendly: bool = False
    needs_conversion: bool = False
    recommendations: list[str] = Field(default_factory=list)


class FrameDjangoAccessResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    orm_accessible: bool = False
    has_raw_file: bool = False
    has_processed_file: bool = False
    active_file_attr: str | None = None
    active_file_name: str | None = None
    file_size: int = 0
    errors: list[str] = Field(default_factory=list)


class FrameFileInfoResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    filename: str
    size_bytes: int
    size_mb: float
    created_at: datetime
    modified_at: datetime
    extension: str
    exists: bool = True


class FrameAnonymizationStatisticsResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    requests: dict[str, int]
    frames: dict[str, int]
    storage: dict[str, float | int]
    video_id: int | None = None
    error: str | None = None


__all__ = [
    "FrameAnonymizationStatisticsResult",
    "FrameDjangoAccessResult",
    "FrameFileInfoResult",
    "FrameStreamingCompatibilityResult",
    "FrameVideoAnalysisResult",
]
