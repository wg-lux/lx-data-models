from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class LabelVideoSegmentSummaryPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    id: int
    label_id: int | None = None
    label_name: str
    source_name: str | None = None
    segment_origin: str
    prediction_meta_id: int | None = None
    start_frame_number: int
    end_frame_number: int
    start_time: float | None = None
    end_time: float | None = None
    export_segment: bool = False


class LabelVideoSegmentFrameClassificationPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    frame_filename: str
    frame_file_path: str
    frame_url: str
    all_classifications: list[dict[str, object]] = Field(default_factory=list)
    frame_id: int


class LabelVideoSegmentTimeSegmentPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    segment_id: int
    segment_start: int
    segment_end: int
    start_time: float | None = None
    end_time: float | None = None
    frames: list[LabelVideoSegmentFrameClassificationPayload] = Field(
        default_factory=list
    )


__all__ = [
    "LabelVideoSegmentFrameClassificationPayload",
    "LabelVideoSegmentSummaryPayload",
    "LabelVideoSegmentTimeSegmentPayload",
]
