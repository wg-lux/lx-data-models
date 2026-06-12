from __future__ import annotations

from typing import Literal, TypedDict

from pydantic import BaseModel, ConfigDict, Field

AnonymizationOverviewFileType = Literal["video", "pdf", "unknown"]
AnonymizationOverviewMediaType = Literal["video", "pdf"]
AnonymizationStatusValue = Literal[
    "not_started",
    "extracting_frames",
    "processing_anonymization",
    "done_processing_anonymization",
    "validated",
    "failed",
    "started",
    "anonymized",
]


class AnonymizationStatusInfoData(TypedDict):
    media_type: AnonymizationOverviewMediaType | None
    type: AnonymizationOverviewMediaType | None
    anonymization_status: AnonymizationStatusValue | str | None
    status: AnonymizationStatusValue | str | None
    integrity_status: str
    integrity_error: str


class AnonymizationStatusResponseData(TypedDict):
    file_id: int
    file_type: str
    anonymization_status: str
    integrity_status: str
    integrity_error: str
    processing_locked: bool


class StartAnonymizationResponseData(TypedDict):
    detail: str
    file_id: int
    file_type: str
    processing_locked: bool


class ClearProcessingLocksResponseData(TypedDict):
    detail: str
    cleared_count: int
    file_type_filter: str | None


class OverviewUploadJobData(TypedDict, total=False):
    sensitive_meta_id: int
    content_hash: str


class OverviewUploadJobPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    sensitive_meta_id: int | None = Field(default=None, ge=1)
    content_hash: str = Field(default="", min_length=1)

    def to_data(self) -> OverviewUploadJobData:
        data: OverviewUploadJobData = {}
        if self.sensitive_meta_id is not None:
            data["sensitive_meta_id"] = self.sensitive_meta_id
        if self.content_hash:
            data["content_hash"] = self.content_hash
        return data


__all__ = [
    "AnonymizationOverviewFileType",
    "AnonymizationOverviewMediaType",
    "AnonymizationStatusInfoData",
    "AnonymizationStatusResponseData",
    "AnonymizationStatusValue",
    "ClearProcessingLocksResponseData",
    "OverviewUploadJobData",
    "OverviewUploadJobPayload",
    "StartAnonymizationResponseData",
]
