"""Validated saved cohort definitions; membership is recomputed on explicit preview."""

from __future__ import annotations

from datetime import date
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .study_metadata import StudyMetadata

PositiveId = Annotated[int, Field(strict=True, gt=0)]


class CohortFilters(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    date_from: str | None = None
    date_to: str | None = None
    center_key: str | None = None
    examination_name: str | None = None
    document_type: str | None = None
    finding: str | None = None
    annotation_label: str | None = None
    has_report: bool | None = None
    has_video: bool | None = None
    limit: int = Field(default=100, ge=1, le=500)

    @model_validator(mode="after")
    def valid_filters(self) -> Self:
        dates: list[date | None] = []
        for key, value in (("date_from", self.date_from), ("date_to", self.date_to)):
            normalized = value.strip() if value else ""
            if not normalized:
                dates.append(None)
                continue
            try:
                parsed = date.fromisoformat(normalized)
            except ValueError as exc:
                raise ValueError(f"{key} must use YYYY-MM-DD format.") from exc
            if parsed.isoformat() != normalized:
                raise ValueError(f"{key} must use YYYY-MM-DD format.")
            dates.append(parsed)
        start, end = dates
        if start is not None and end is not None and end < start:
            raise ValueError("date_to must be greater than or equal to date_from.")
        return self


class CohortDefinitionFields(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=255)
    hypothesis: str = Field(min_length=1, max_length=10000)
    filters: CohortFilters = Field(default_factory=CohortFilters)
    study_metadata: StudyMetadata = Field(default_factory=StudyMetadata)


class CohortDefinition(CohortDefinitionFields):
    study_id: PositiveId | None = None
    dataset_ids: list[PositiveId] = Field(default_factory=list, max_length=500)

    @model_validator(mode="after")
    def unique_datasets(self) -> Self:
        if len(self.dataset_ids) != len(set(self.dataset_ids)):
            raise ValueError("Dataset IDs must be unique.")
        return self


class CohortDatasetLink(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    cohort_id: PositiveId
    linked: bool


class CohortPreviewDefinition(CohortDefinition):
    """Optional owned saved cohort supplies explicitly imported examination scope."""

    cohort_id: PositiveId | None = None
