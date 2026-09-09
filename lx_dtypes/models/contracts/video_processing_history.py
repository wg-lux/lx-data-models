from __future__ import annotations

from datetime import datetime
from typing import Literal, TypedDict

from pydantic import BaseModel, ConfigDict, Field

type VideoProcessingHistoryOperation = Literal[
    "mask_overlay",
    "frame_removal",
    "analysis",
    "reprocessing",
    "ai_temporal_inference",
]

type VideoProcessingHistoryStatus = Literal[
    "pending",
    "running",
    "success",
    "failure",
    "cancelled",
]


class VideoProcessingHistorySummaryData(TypedDict):
    video_hash: str
    operation: VideoProcessingHistoryOperation
    status: VideoProcessingHistoryStatus
    output_file: str
    details: str
    task_id: str
    created_at: datetime
    completed_at: datetime | None
    duration_seconds: float | None


class VideoProcessingHistorySummaryPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    video_hash: str = Field(min_length=1)
    operation: VideoProcessingHistoryOperation
    status: VideoProcessingHistoryStatus
    output_file: str = ""
    details: str = ""
    task_id: str = ""
    created_at: datetime
    completed_at: datetime | None = None
    duration_seconds: float | None = None

    def to_summary_data(self) -> VideoProcessingHistorySummaryData:
        return {
            "video_hash": self.video_hash,
            "operation": self.operation,
            "status": self.status,
            "output_file": self.output_file,
            "details": self.details,
            "task_id": self.task_id,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "duration_seconds": self.duration_seconds,
        }


__all__ = [
    "VideoProcessingHistoryOperation",
    "VideoProcessingHistoryStatus",
    "VideoProcessingHistorySummaryData",
    "VideoProcessingHistorySummaryPayload",
]
