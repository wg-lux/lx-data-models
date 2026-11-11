from __future__ import annotations

from datetime import datetime

from pydantic import Field

from lx_dtypes.models.model import FrozenContractModel


class FrameVideoAnalysisResult(FrozenContractModel):
    file_readable: bool = False
    has_video_stream: bool = False
    has_audio_stream: bool = False
    duration: float | None = None
    codec: str | None = None
    resolution: str | None = None
    frame_count: str | int | None = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class FrameStreamingCompatibilityResult(FrozenContractModel):
    web_compatible: bool = False
    streaming_friendly: bool = False
    needs_conversion: bool = False
    recommendations: list[str] = Field(default_factory=list)


class FrameDjangoAccessResult(FrozenContractModel):
    orm_accessible: bool = False
    has_raw_file: bool = False
    has_processed_file: bool = False
    active_file_attr: str | None = None
    active_file_name: str | None = None
    file_size: int = 0
    errors: list[str] = Field(default_factory=list)


class FrameFileInfoResult(FrozenContractModel):
    filename: str
    size_bytes: int
    size_mb: float
    created_at: datetime
    modified_at: datetime
    extension: str
    exists: bool = True


class FrameAnonymizationStatisticsResult(FrozenContractModel):
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
