# /lx-data-models/lx_dtypes/models/contracts/frame_annotation.py
from __future__ import annotations

from typing import Literal, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator

from lx_dtypes.models.contracts.information_source import normalize_name_reference
from lx_dtypes.models.contracts.json_types import JsonObject


class FrameAnnotationLabelOptionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    id: int
    name: str


class FrameAnnotationQueueSpecPayload(BaseModel):
    """
    Validated transport contract for frame annotation queue requests.

    This payload intentionally contains only JSON/task-safe values:
    primitive IDs, strings, booleans, and sets of IDs. Django ORM objects are
    resolved by the endoreg_db adapter layer.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        arbitrary_types_allowed=True,
    )

    limit: int
    task_mode: str = "random"
    video_id: int | None = None
    label_set_id: int | None = None
    target_label_id: int | None = None
    filter_label_id: int | None = None
    information_source_name: str = "manual_annotation"
    annotator: str = ""
    exclude_annotated: bool = True
    ai_dataset_id: int | None = None
    sampling_strategy: str = "balanced"
    prediction_segments_only: bool = True
    exclude_frame_ids: set[int] = Field(default_factory=set)
    require_extracted_frames: bool = True
    require_raw_video: bool = False
    require_processed_video: bool = False
    require_streamable_video_artifact: bool = False

    @field_validator("information_source_name", mode="before")
    @classmethod
    def normalize_information_source_name(cls, value: str | None) -> str:
        return normalize_name_reference(value, default="manual_annotation")


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
    frame_file_type: str | None = None
    decoded_frame_stream_path: str | None = None


class FrameAnnotationQueueResultPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    tasks: list[FrameAnnotationTaskPayload]
    selection_strategy: str
    label_distribution: list[JsonObject] = Field(default_factory=list)
    selected_label_counts: dict[str, int] = Field(default_factory=dict)
    segment_bucket_counts: dict[str, int] = Field(default_factory=dict)
    annotation_bucket_counts: dict[str, int] = Field(default_factory=dict)
    bucket_counts: dict[str, int] = Field(default_factory=dict)


class FrameAnnotationRandomTaskResponsePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    status: Literal["success"] = "success"
    task: FrameAnnotationTaskPayload
    tasks: list[FrameAnnotationTaskPayload]
    count: int
    task_mode: str
    selection_strategy: str
    dataset_frame_filter: str
    prediction_segments_only: bool
    frame_file_type: str | None = None
    label_group_id: int | None = None
    target_label: str | None = None
    filter_label: str | None = None
    ai_dataset_id: int | None = None
    ai_dataset_name: str | None = None
    ai_dataset_type: str | None = None
    label_distribution: list[dict[str, int]] = Field(default_factory=list)
    selected_label_counts: dict[str, int] = Field(default_factory=dict)
    segment_bucket_counts: dict[str, int] = Field(default_factory=dict)
    annotation_bucket_counts: dict[str, int] = Field(default_factory=dict)
    bucket_counts: dict[str, int] = Field(default_factory=dict)

    def to_response_dict(self) -> JsonObject:
        return cast(JsonObject, self.model_dump(mode="json", exclude_none=True))


class FrameAnnotationSkipResponsePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    status: Literal["success"] = "success"
    skipped_frame_id: int
    video_id: int
    annotator: str
    reason: str
    pruned_unused_frames: int
    next_task: FrameAnnotationTaskPayload | None = None

    def to_response_dict(self) -> JsonObject:
        return cast(JsonObject, self.model_dump(mode="json", exclude_none=True))


__all__ = [
    "FrameAnnotationAnnotationPayload",
    "FrameAnnotationLabelOptionPayload",
    "FrameAnnotationQueueResultPayload",
    "FrameAnnotationQueueSpecPayload",
    "FrameAnnotationRandomTaskResponsePayload",
    "FrameAnnotationSkipResponsePayload",
    "FrameAnnotationTaskPayload",
]
