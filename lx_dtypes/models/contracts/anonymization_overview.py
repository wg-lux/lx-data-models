from __future__ import annotations

from datetime import datetime
from typing import Literal, TypedDict
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

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
UploadJobMonitoringStatus = Literal[
    "pending",
    "processing",
    "retrying",
    "anonymized",
    "error",
    "lost",
]
UploadJobIngestMode = Literal["api", "watcher"]
UploadJobCleanupStatus = Literal[
    "pending",
    "eligible",
    "deleting",
    "completed",
    "skipped",
]
ImportErrorCode = Literal[
    "",
    "dispatch_unavailable",
    "duplicate_content",
    "invalid_configuration",
    "invalid_input",
    "media_integrity_failed",
    "processing_failed",
    "source_missing",
]
HlsArtifactKind = Literal["raw", "processed"]
HlsMaterializationStatus = Literal["queued", "materializing", "ready", "failed"]
HlsMaterializationErrorCode = Literal[
    "",
    "dispatch_failed",
    "inconsistent_artifact",
    "materialization_failed",
    "validation_failed",
    "stale_attempt",
]
ImportMonitoringAction = Literal["safe_reimport", "delete"]


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


class OverviewHlsMaterializationData(TypedDict):
    artifact_kind: HlsArtifactKind
    status: HlsMaterializationStatus
    triggering_upload_job_id: str | None
    source_generation_id: str
    target_generation_id: str
    segment_count: int
    error_code: HlsMaterializationErrorCode
    created_at: str
    updated_at: str


class OverviewUploadJobMonitoringData(TypedDict):
    id: str
    status: UploadJobMonitoringStatus
    ingest_mode: UploadJobIngestMode
    source_system: str
    source_center_key: str | None
    original_filename: str
    source_file_persisted: bool
    cleanup_status: UploadJobCleanupStatus
    allowed_actions: list[ImportMonitoringAction]
    error_code: ImportErrorCode
    error_detail: str
    retryable: bool
    retry_count: int
    max_retries: int
    next_retry_at: str | None
    last_attempt_at: str | None
    created_at: str
    updated_at: str


class OverviewHlsMaterializationPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    artifact_kind: HlsArtifactKind
    status: HlsMaterializationStatus
    triggering_upload_job_id: UUID | None = None
    source_generation_id: UUID
    target_generation_id: UUID
    segment_count: int = Field(ge=0)
    error_code: HlsMaterializationErrorCode = ""
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def validate_state(self) -> OverviewHlsMaterializationPayload:
        if self.status == "ready" and self.segment_count < 1:
            raise ValueError("ready HLS materialization requires at least one segment")
        if self.status == "failed" and not self.error_code:
            raise ValueError("failed HLS materialization requires an error_code")
        if self.status != "failed" and self.error_code:
            raise ValueError("only failed HLS materialization may contain error_code")
        return self

    def to_data(self) -> OverviewHlsMaterializationData:
        return OverviewHlsMaterializationData(
            artifact_kind=self.artifact_kind,
            status=self.status,
            triggering_upload_job_id=(
                str(self.triggering_upload_job_id)
                if self.triggering_upload_job_id is not None
                else None
            ),
            source_generation_id=str(self.source_generation_id),
            target_generation_id=str(self.target_generation_id),
            segment_count=self.segment_count,
            error_code=self.error_code,
            created_at=self.created_at.isoformat(),
            updated_at=self.updated_at.isoformat(),
        )


class OverviewUploadJobMonitoringPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    id: UUID
    status: UploadJobMonitoringStatus
    ingest_mode: UploadJobIngestMode
    source_system: str = Field(min_length=1)
    source_center_key: str | None = None
    original_filename: str = ""
    source_file_persisted: bool
    cleanup_status: UploadJobCleanupStatus
    allowed_actions: list[ImportMonitoringAction] = Field(default_factory=list)
    error_code: ImportErrorCode = ""
    error_detail: str = ""
    retryable: bool = False
    retry_count: int = Field(default=0, ge=0)
    max_retries: int = Field(default=0, ge=0)
    next_retry_at: datetime | None = None
    last_attempt_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def validate_state(self) -> OverviewUploadJobMonitoringPayload:
        if self.status == "retrying":
            if not self.retryable:
                raise ValueError("retrying upload job must be retryable")
            if not self.error_code:
                raise ValueError("retrying upload job requires an error_code")
            if self.retry_count < 1:
                raise ValueError("retrying upload job requires retry_count >= 1")
            if self.max_retries < self.retry_count:
                raise ValueError("retry_count must not exceed max_retries")
            if self.next_retry_at is None:
                raise ValueError("retrying upload job requires next_retry_at")
        elif self.retryable or self.next_retry_at is not None:
            raise ValueError("only retrying upload jobs may be retryable or scheduled")

        if self.status in {"error", "lost"} and not self.error_code:
            raise ValueError("terminal upload job failure requires an error_code")
        if self.status not in {"retrying", "error", "lost"} and (
            self.error_code or self.error_detail
        ):
            raise ValueError("non-failed upload job must not expose error state")
        expected_actions: list[ImportMonitoringAction]
        if self.status == "anonymized":
            expected_actions = ["delete"]
        elif (
            self.status in {"error", "lost"} and self.error_code != "duplicate_content"
        ):
            expected_actions = ["safe_reimport", "delete"]
        else:
            expected_actions = []
        if self.allowed_actions != expected_actions:
            raise ValueError("allowed_actions are inconsistent with upload job state")
        return self

    def to_data(self) -> OverviewUploadJobMonitoringData:
        return OverviewUploadJobMonitoringData(
            id=str(self.id),
            status=self.status,
            ingest_mode=self.ingest_mode,
            source_system=self.source_system,
            source_center_key=self.source_center_key,
            original_filename=self.original_filename,
            source_file_persisted=self.source_file_persisted,
            cleanup_status=self.cleanup_status,
            allowed_actions=list(self.allowed_actions),
            error_code=self.error_code,
            error_detail=self.error_detail,
            retryable=self.retryable,
            retry_count=self.retry_count,
            max_retries=self.max_retries,
            next_retry_at=(
                self.next_retry_at.isoformat()
                if self.next_retry_at is not None
                else None
            ),
            last_attempt_at=(
                self.last_attempt_at.isoformat()
                if self.last_attempt_at is not None
                else None
            ),
            created_at=self.created_at.isoformat(),
            updated_at=self.updated_at.isoformat(),
        )


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
    "HlsArtifactKind",
    "HlsMaterializationErrorCode",
    "HlsMaterializationStatus",
    "ImportErrorCode",
    "ImportMonitoringAction",
    "OverviewHlsMaterializationData",
    "OverviewHlsMaterializationPayload",
    "OverviewUploadJobData",
    "OverviewUploadJobMonitoringData",
    "OverviewUploadJobMonitoringPayload",
    "OverviewUploadJobPayload",
    "StartAnonymizationResponseData",
    "UploadJobCleanupStatus",
    "UploadJobIngestMode",
    "UploadJobMonitoringStatus",
]
