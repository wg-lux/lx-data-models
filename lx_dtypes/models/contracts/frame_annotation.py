from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FrameAnnotationLabelOptionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    id: int
    name: str


class FrameAnnotationAnnotationPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    id: int
    label_id: int
    label_name: str
    value: bool
    float_value: float | None = None
    annotator: str | None = None
    information_source_name: str | None = None
    model_meta_id: int | None = None
    external_annotation_id: str | None = None


class FrameAnnotationTaskPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    frame_id: int
    video_id: int
    frame_number: int
    relative_path: str
    frame_stream_path: str
    annotation_mode: str = "multilabel"
    label_options: list[FrameAnnotationLabelOptionPayload] = Field(default_factory=list)
    manual_annotations: list[FrameAnnotationAnnotationPayload] = Field(
        default_factory=list
    )
    prediction_annotations: list[FrameAnnotationAnnotationPayload] = Field(
        default_factory=list
    )
    manual_positive_label_ids: list[int] = Field(default_factory=list)
    prediction_positive_label_ids: list[int] = Field(default_factory=list)
    suggested_label_ids: list[int] = Field(default_factory=list)
    dataset_selection_label_id: int | None = None
    dataset_selection_label_name: str | None = None
    dataset_selection_source: str | None = None
    dataset_bucket: str | None = None


class FrameAnnotationQueueResultPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    tasks: list[FrameAnnotationTaskPayload]
    selection_strategy: str
    label_distribution: list[dict[str, Any]] = Field(default_factory=list)
    selected_label_counts: dict[str, int] = Field(default_factory=dict)
    segment_bucket_counts: dict[str, int] = Field(default_factory=dict)
    annotation_bucket_counts: dict[str, int] = Field(default_factory=dict)
    bucket_counts: dict[str, int] = Field(default_factory=dict)


__all__ = [
    "FrameAnnotationAnnotationPayload",
    "FrameAnnotationLabelOptionPayload",
    "FrameAnnotationQueueResultPayload",
    "FrameAnnotationTaskPayload",
]
