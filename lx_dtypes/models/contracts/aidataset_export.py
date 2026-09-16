from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from lx_dtypes.models.ledger.p_video.Pydantic import PatientVideoFile

from .json_types import JsonObject


class AIDataSetFrameLabelExport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    id: int
    name: str
    labelset_name: str | None = None


class AIDataSetFrameAnnotationExport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    annotation_id: int
    frame_id: int
    frame_number: int
    timestamp: float | None = None
    relative_path: str
    file_path: str | None = None
    patient_video_file_uuid: str
    video_id: int
    video_uuid: str
    video_hash: str
    original_file_name: str | None = None
    label: AIDataSetFrameLabelExport
    value: bool
    confidence: float | None = None
    annotator: str | None = None
    information_source_name: str | None = None
    model_meta_id: int | None = None
    external_annotation_id: str | None = None
    date_created: datetime
    date_modified: datetime


class AIDataSetExportSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    image_annotation_count: int = 0
    video_annotation_count: int = 0
    frame_count: int = 0
    video_count: int = 0
    label_count: int = 0


class AIDataSetExportPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    schema_version: str = "1.0"
    dataset_id: int
    name: str | None = None
    description: str | None = None
    dataset_type: str
    ai_model_type: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    summary: AIDataSetExportSummary
    patient_videos: dict[str, PatientVideoFile] = Field(default_factory=dict)
    frame_annotations: list[AIDataSetFrameAnnotationExport] = Field(
        default_factory=list
    )

    def to_json_object(self) -> JsonObject:
        return self.model_dump(mode="json")


AIDataSetExportPayload.model_rebuild()

__all__ = [
    "AIDataSetExportPayload",
    "AIDataSetExportSummary",
    "AIDataSetFrameAnnotationExport",
    "AIDataSetFrameLabelExport",
]
