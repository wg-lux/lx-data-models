from __future__ import annotations

from typing import Literal, TypedDict

from pydantic import BaseModel, ConfigDict, Field

type VideoSegmentValidationNull = None
type VideoSegmentValidationText = str | VideoSegmentValidationNull

type OutsideFrameBlackeningKind = Literal["outside_frame_blackening"]


class OutsideFrameBlackeningHistoryConfigData(TypedDict):
    kind: str
    only_validated: bool
    queue: str


class OutsideFrameBlackeningHistoryConfigPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    kind: OutsideFrameBlackeningKind = Field(default="outside_frame_blackening")
    only_validated: bool
    queue: str = Field(min_length=1)

    def to_config_data(self) -> OutsideFrameBlackeningHistoryConfigData:
        return {
            "kind": self.kind,
            "only_validated": self.only_validated,
            "queue": self.queue,
        }


class PostValidationRebuildSummaryData(TypedDict):
    id: int
    status: str
    task_id: VideoSegmentValidationText
    details: str
    output_file: str
    created_at: VideoSegmentValidationText
    completed_at: VideoSegmentValidationText


class PostValidationRebuildSummaryPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    id: int
    status: str = Field(min_length=1)
    task_id: VideoSegmentValidationText = None
    details: str = ""
    output_file: str = ""
    created_at: VideoSegmentValidationText = None
    completed_at: VideoSegmentValidationText = None

    def to_summary_data(self) -> PostValidationRebuildSummaryData:
        return {
            "id": self.id,
            "status": self.status,
            "task_id": self.task_id,
            "details": self.details,
            "output_file": self.output_file,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }


__all__ = [
    "OutsideFrameBlackeningHistoryConfigData",
    "OutsideFrameBlackeningHistoryConfigPayload",
    "OutsideFrameBlackeningKind",
    "PostValidationRebuildSummaryData",
    "PostValidationRebuildSummaryPayload",
    "VideoSegmentValidationNull",
    "VideoSegmentValidationText",
]
