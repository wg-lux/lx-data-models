from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .json_types import JsonObject

AnonymizationMetricsMediaType = Literal["video", "pdf"]


class AnonymizationMetricsFiltersPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    date_from: datetime
    date_to: datetime
    media_type: AnonymizationMetricsMediaType | None = None
    center_id: int | None = Field(default=None, ge=1)
    document_type: str | None = None
    source_system: str | None = None


class AnonymizationMetricsQueryBoundsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    max_window_days: int = Field(ge=1)
    max_phi_region_match_annotations: int = Field(ge=1)


class AnonymizationWorkflowMetricsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    status_counts: dict[str, int]
    pending_validation_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)
    lost_count: int = Field(ge=0)
    failed_or_lost_count: int = Field(ge=0)
    validation_event_count: int = Field(ge=0)
    avg_seconds_to_validation: float | None = None
    min_seconds_to_validation: float | None = None
    max_seconds_to_validation: float | None = None
    median_seconds_to_validation: float | None = None


class AnonymizationFieldQualityPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    field_name: str
    support: int = Field(ge=0)
    changed_count: int = Field(ge=0)
    changed_rate: float | None = None
    exact_match_count: int = Field(ge=0)
    exact_match_rate: float | None = None
    mean_similarity: float | None = None
    missing_after_validation_count: int = Field(ge=0)


class AnonymizationPhiRegionMetricsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    proposal_count: int = Field(ge=0)
    human_annotation_count: int = Field(ge=0)
    matched_count: int | None = Field(default=None, ge=0)
    precision: float | None = None
    recall: float | None = None
    matching_evaluated: bool
    matching_annotation_count: int = Field(ge=0)
    max_matching_annotations: int = Field(ge=1)


class AnonymizationQualityMetricsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    evaluated_event_count: int = Field(ge=0)
    residual_phi_detected_count: int = Field(ge=0)
    residual_ocr_match_count: int = Field(ge=0)
    phi_region_false_negative_count: int = Field(ge=0)
    raw_artifact_residual_count: int = Field(ge=0)
    missing_sensitive_meta_deletion_count: int = Field(ge=0)
    sensitive_meta_deletion_status_counts: dict[str, int]
    sensitive_meta_policy_counts: dict[str, int]


class AnonymizationMetricsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    schema_version: str = "1.0"
    filters: AnonymizationMetricsFiltersPayload
    query_bounds: AnonymizationMetricsQueryBoundsPayload
    workflow: AnonymizationWorkflowMetricsPayload
    field_quality: list[AnonymizationFieldQualityPayload]
    phi_regions: AnonymizationPhiRegionMetricsPayload
    quality: AnonymizationQualityMetricsPayload

    def to_json_object(self) -> JsonObject:
        return self.model_dump(mode="json")


__all__ = [
    "AnonymizationFieldQualityPayload",
    "AnonymizationMetricsFiltersPayload",
    "AnonymizationMetricsMediaType",
    "AnonymizationMetricsPayload",
    "AnonymizationMetricsQueryBoundsPayload",
    "AnonymizationPhiRegionMetricsPayload",
    "AnonymizationQualityMetricsPayload",
    "AnonymizationWorkflowMetricsPayload",
]
