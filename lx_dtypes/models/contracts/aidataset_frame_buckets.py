from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class AIDataSetTargetFrameBucket(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        return self.value


class AIDataSetFrameBucketCount(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    bucket: AIDataSetTargetFrameBucket
    frame_count: int = 0


class AIDataSetLabelDistributionEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    label_id: int
    label_name: str
    frame_positive: int = 0
    frame_negative: int = 0
    segment_count: int = 0
    total: int = 0


class AIDataSetLabelFrameBucketCount(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    label_id: int
    label_name: str
    frame_count: int = 0


class AIDataSetFrameBucketSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    image_annotation_count: int = 0
    video_annotation_count: int = 0
    annotation_frame_count: int = 0
    segment_frame_count: int = 0
    merged_frame_count: int = 0
    video_count: int = 0
    label_count: int = 0


class AIDataSetFrameBucketDistribution(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    schema_version: str = "1.0"
    dataset_id: int
    name: str | None = None
    dataset_type: str
    ai_model_type: str
    is_active: bool
    updated_at: datetime
    label_group_id: int | None = None
    label_group_name: str | None = None
    target_label_id: int | None = None
    target_label_name: str | None = None
    prediction_segments_only: bool = True
    summary: AIDataSetFrameBucketSummary
    target_buckets: list[AIDataSetFrameBucketCount] = Field(default_factory=list)
    label_distribution: list[AIDataSetLabelDistributionEntry] = Field(
        default_factory=list
    )
    annotation_frame_buckets: list[AIDataSetLabelFrameBucketCount] = Field(
        default_factory=list
    )
    segment_frame_buckets: list[AIDataSetLabelFrameBucketCount] = Field(
        default_factory=list
    )
    merged_frame_buckets: list[AIDataSetLabelFrameBucketCount] = Field(
        default_factory=list
    )


__all__ = [
    "AIDataSetFrameBucketCount",
    "AIDataSetFrameBucketDistribution",
    "AIDataSetFrameBucketSummary",
    "AIDataSetLabelDistributionEntry",
    "AIDataSetLabelFrameBucketCount",
    "AIDataSetTargetFrameBucket",
]
