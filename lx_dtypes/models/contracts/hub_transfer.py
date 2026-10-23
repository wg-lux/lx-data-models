from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Literal, NotRequired, TypedDict, cast
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from .json_types import JsonObject, JsonValue
from .study_exchange import StudyExchangeBundle
from .video_provenance import VideoProvenanceBundle, VideoProvenanceRecovery
from .video_segment_timeline import (
    VideoSegmentTimelineCoordinates,
    VideoSegmentTimelineCoordinatesData,
)

type HubTransferJsonScalar = str | int | float | bool | None
type HubTransferJsonValue = (
    HubTransferJsonScalar
    | list["HubTransferJsonValue"]
    | dict[str, "HubTransferJsonValue"]
)
type HubTransferJsonObject = dict[str, HubTransferJsonValue]
type HubTransferSegmentSourceKind = Literal["manual_annotation", "prediction"]
type HubTransferSegmentValidationState = Literal["unvalidated", "validated"]


class HubTransferVideoFilePayloadData(TypedDict):
    raw_video_hash: str
    processed_video_hash: str
    suffix: str | None
    fps: float | None
    duration: float | None
    frame_count: int | None
    width: int | None
    height: int | None


class HubTransferSensitiveMetaPayloadData(TypedDict):
    patient_uuid: str
    examination_uuid: str


class HubTransferVideoStatePayloadData(TypedDict, total=False):
    processing_started: bool
    frames_extracted: bool
    sensitive_meta_processed: bool
    frame_annotations_generated: bool
    anonymized: bool
    anonymization_validated: bool
    outside_segments_removed: bool
    segment_annotations_created: bool
    segment_annotations_validated: bool
    processed_file_sha256: str


class HubTransferProcessingHistoryPayloadData(TypedDict):
    file_hash: str
    success: bool


class HubTransferFrameAnnotationPayloadData(TypedDict):
    annotation_id: int | str
    raw_video_hash: str
    frame_number: int
    frame_relative_path: str
    frame_timestamp: float | None
    label_name: str
    value: bool
    float_value: float | None
    information_source_name: str


class HubTransferSegmentProvenancePayloadData(TypedDict):
    information_source_name: str


class HubTransferVideoSegmentPayloadData(TypedDict):
    source_node_key: str
    source_segment_id: int | str
    raw_video_hash: str
    start_frame_number: int
    end_frame_number_exclusive: int
    label_name: str
    source_kind: HubTransferSegmentSourceKind
    validation_state: HubTransferSegmentValidationState
    export_segment: bool
    anonymous_provenance: HubTransferSegmentProvenancePayloadData
    timeline_coordinates: VideoSegmentTimelineCoordinatesData
    model_name: NotRequired[str]
    model_version: NotRequired[str]


class HubTransferReportPayloadData(TypedDict):
    template_name: str
    template_version: str
    template_hash: str
    status: Literal["final"]
    version: int
    is_active: Literal[True]


class HubTransferVideoResourceRowsData(TypedDict, total=False):
    video_file: HubTransferVideoFilePayloadData
    sensitive_meta: HubTransferSensitiveMetaPayloadData
    video_state: HubTransferVideoStatePayloadData
    processing_history: HubTransferProcessingHistoryPayloadData
    video_segments: list[HubTransferVideoSegmentPayloadData]
    frame_annotations: list[HubTransferFrameAnnotationPayloadData]
    reports: list[HubTransferReportPayloadData]


class HubTransferRawPdfFilePayloadData(TypedDict):
    pdf_hash: str
    anonymized_text: str


class HubTransferRawPdfStatePayloadData(TypedDict, total=False):
    processing_started: bool
    text_meta_extracted: bool
    sensitive_meta_processed: bool
    anonymized: bool
    anonymization_validated: bool
    processed_file_sha256: str


class HubTransferReportResourceRowsData(TypedDict, total=False):
    raw_pdf_file: HubTransferRawPdfFilePayloadData
    sensitive_meta: HubTransferSensitiveMetaPayloadData
    raw_pdf_state: HubTransferRawPdfStatePayloadData
    processing_history: HubTransferProcessingHistoryPayloadData
    reports: list[HubTransferReportPayloadData]


class HubTransferProcessingSnapshotData(TypedDict):
    sender_processing_success: bool


class HubTransferProvenanceData(TypedDict, total=False):
    video_frame_provenance: JsonObject
    video_provenance_recovery: JsonObject
    entrypoint: str
    source_node_key: str
    source_center_key: str
    target_node_key: str
    transfer_mode: str
    processing_policy: str
    cleanup_policy: str


class HubTransferVideoTransferPayloadData(TypedDict):
    transfer_key: str
    source_node_key: str
    target_node_key: str
    source_center_key: str
    resource_kind: Literal["video"]
    resource_hash: str
    transfer_mode: str
    processing_policy: str
    processing_intent: str
    cleanup_policy: str
    payload_schema_version: Literal["7.0"]
    resource_rows: HubTransferVideoResourceRowsData
    processing_snapshot: HubTransferProcessingSnapshotData
    provenance: NotRequired[HubTransferProvenanceData]


class HubTransferReportTransferPayloadData(TypedDict):
    transfer_key: str
    source_node_key: str
    target_node_key: str
    source_center_key: str
    resource_kind: Literal["report"]
    resource_hash: str
    transfer_mode: str
    processing_policy: str
    processing_intent: str
    cleanup_policy: str
    payload_schema_version: Literal["7.0"]
    resource_rows: HubTransferReportResourceRowsData
    processing_snapshot: HubTransferProcessingSnapshotData
    provenance: NotRequired[HubTransferProvenanceData]


class _StrictPayload(BaseModel):
    model_config = ConfigDict(
        extra="forbid", frozen=True, strict=True, str_strip_whitespace=True
    )


class HubTransferVideoFilePayload(_StrictPayload):
    raw_video_hash: str = Field(min_length=1)
    processed_video_hash: str = Field(min_length=1)
    suffix: str | None = None
    fps: float | None = Field(default=None, ge=0)
    duration: float | None = Field(default=None, ge=0)
    frame_count: int | None = Field(default=None, ge=0)
    width: int | None = Field(default=None, ge=1)
    height: int | None = Field(default=None, ge=1)


HUB_RECORD_PSEUDONYM_UUID_VERSION = 8


def require_hub_record_pseudonym(value: UUID) -> UUID:
    """Hub records carry site-salted UUIDv8 pseudonyms, never site-local UUIDs.

    The receiver cannot verify the keyed derivation; the version check rejects
    the legacy path that sent persisted random (version 4) local UUIDs.
    """
    if value.version != HUB_RECORD_PSEUDONYM_UUID_VERSION:
        raise ValueError(
            "Hub records require site-salted UUIDv8 pseudonyms, not local UUIDs"
        )
    return value


class HubTransferSensitiveMetaPayload(_StrictPayload):
    patient_uuid: UUID = Field(strict=False)
    examination_uuid: UUID = Field(strict=False)

    @field_validator("patient_uuid", "examination_uuid", mode="after")
    @classmethod
    def _require_pseudonyms(cls, value: UUID) -> UUID:
        return require_hub_record_pseudonym(value)


class HubTransferVideoStatePayload(_StrictPayload):
    processing_started: bool | None = None
    frames_extracted: bool | None = None
    sensitive_meta_processed: bool | None = None
    frame_annotations_generated: bool | None = None
    anonymized: bool | None = None
    anonymization_validated: bool | None = None
    outside_segments_removed: bool | None = None
    segment_annotations_created: bool | None = None
    segment_annotations_validated: bool | None = None
    processed_file_sha256: str | None = None


class HubTransferProcessingHistoryPayload(_StrictPayload):
    file_hash: str = Field(min_length=1)
    success: bool


class HubTransferFrameAnnotationPayload(_StrictPayload):
    annotation_id: int | str
    raw_video_hash: str = Field(min_length=1)
    frame_number: int = Field(ge=0)
    frame_relative_path: str = Field(min_length=1)
    frame_timestamp: float | None = Field(default=None, ge=0)
    label_name: str = Field(min_length=1)
    value: bool
    float_value: float | None = None
    information_source_name: str = Field(min_length=1)


class HubTransferSegmentProvenancePayload(_StrictPayload):
    information_source_name: str = Field(min_length=1)


class HubTransferVideoSegmentPayload(_StrictPayload):
    source_node_key: str = Field(min_length=1)
    source_segment_id: int | str
    raw_video_hash: str = Field(min_length=1)
    start_frame_number: int = Field(ge=0)
    end_frame_number_exclusive: int = Field(ge=1)
    label_name: str = Field(min_length=1)
    source_kind: HubTransferSegmentSourceKind
    validation_state: HubTransferSegmentValidationState
    export_segment: bool
    anonymous_provenance: HubTransferSegmentProvenancePayload
    timeline_coordinates: VideoSegmentTimelineCoordinates
    model_name: str | None = None
    model_version: str | None = None

    @field_validator("source_segment_id", mode="before")
    @classmethod
    def _normalize_source_segment_id(cls, value: int | str) -> int | str:
        if isinstance(value, bool) or not isinstance(value, (int, str)):
            raise ValueError(  # noqa: TRY004 - Pydantic validation failure
                "source_segment_id must be an integer or string"
            )
        if isinstance(value, str):
            normalized = value.strip()
            if not normalized:
                raise ValueError("source_segment_id must not be blank")
            return normalized
        return value

    @model_validator(mode="after")
    def _validate_segment_contract(self) -> HubTransferVideoSegmentPayload:
        if self.end_frame_number_exclusive <= self.start_frame_number:
            raise ValueError(
                "end_frame_number_exclusive must exceed start_frame_number"
            )
        generation = self.timeline_coordinates.generation
        if (generation.first_frame_number, generation.last_frame_number) != (
            self.start_frame_number,
            self.end_frame_number_exclusive - 1,
        ):
            raise ValueError(
                "timeline_coordinates must describe the first and last included frame"
            )
        has_model_name = self.model_name is not None
        has_model_version = self.model_version is not None
        if has_model_name != has_model_version:
            raise ValueError("model_name and model_version must be supplied together")
        if has_model_name and (
            self.source_kind != "prediction" or not self.export_segment
        ):
            raise ValueError(
                "model metadata is permitted only for exported prediction segments"
            )
        return self


class HubTransferReportPayload(_StrictPayload):
    template_name: str = Field(min_length=1)
    template_version: str = ""
    template_hash: str = ""
    status: Literal["final"] = "final"
    version: int = Field(default=1, ge=1)
    is_active: Literal[True] = True


class HubTransferVideoResourceRowsPayload(_StrictPayload):
    video_file: HubTransferVideoFilePayload
    sensitive_meta: HubTransferSensitiveMetaPayload
    video_state: HubTransferVideoStatePayload
    processing_history: HubTransferProcessingHistoryPayload
    video_segments: list[HubTransferVideoSegmentPayload] = Field(default_factory=list)
    frame_annotations: list[HubTransferFrameAnnotationPayload] = Field(
        default_factory=list
    )
    reports: list[HubTransferReportPayload] = Field(default_factory=list)


class HubTransferRawPdfFilePayload(_StrictPayload):
    pdf_hash: str = Field(min_length=1)
    anonymized_text: str = Field(min_length=1)


class HubTransferRawPdfStatePayload(_StrictPayload):
    processing_started: bool | None = None
    text_meta_extracted: bool | None = None
    sensitive_meta_processed: bool | None = None
    anonymized: bool | None = None
    anonymization_validated: bool | None = None
    processed_file_sha256: str | None = None


class HubTransferReportResourceRowsPayload(_StrictPayload):
    raw_pdf_file: HubTransferRawPdfFilePayload
    sensitive_meta: HubTransferSensitiveMetaPayload
    raw_pdf_state: HubTransferRawPdfStatePayload
    processing_history: HubTransferProcessingHistoryPayload
    reports: list[HubTransferReportPayload] = Field(default_factory=list)


class HubTransferProcessingSnapshotPayload(_StrictPayload):
    sender_processing_success: bool


class HubTransferProvenancePayload(_StrictPayload):
    video_frame_provenance: VideoProvenanceBundle | None = None
    video_provenance_recovery: VideoProvenanceRecovery | None = None
    entrypoint: str | None = None
    source_node_key: str | None = None
    source_center_key: str | None = None
    target_node_key: str | None = None
    transfer_mode: str | None = None
    processing_policy: str | None = None
    cleanup_policy: str | None = None


class _HubTransferPayload(_StrictPayload):
    transfer_key: str = Field(min_length=1)
    source_node_key: str = Field(min_length=1)
    target_node_key: str = Field(min_length=1)
    source_center_key: str = Field(min_length=1)
    resource_hash: str = Field(min_length=1)
    transfer_mode: str = Field(min_length=1)
    processing_policy: str = Field(min_length=1)
    processing_intent: str = Field(min_length=1)
    cleanup_policy: str = Field(min_length=1)
    payload_schema_version: Literal["7.0"]
    processing_snapshot: HubTransferProcessingSnapshotPayload
    provenance: HubTransferProvenancePayload | None = None


class HubTransferVideoTransferPayload(_HubTransferPayload):
    resource_kind: Literal["video"]
    resource_rows: HubTransferVideoResourceRowsPayload

    @model_validator(mode="after")
    def _validate_resource_linkage(self) -> HubTransferVideoTransferPayload:
        if self.resource_rows.video_file.raw_video_hash != self.resource_hash:
            raise ValueError("video_file.raw_video_hash must match resource_hash")
        if (
            self.provenance is not None
            and self.provenance.video_frame_provenance is not None
        ):
            frames = self.provenance.video_frame_provenance.transformations
            if frames[0].source.content_hash != self.resource_hash:
                raise ValueError(
                    "Frame provenance must start at the transferred recording"
                )
            if (
                frames[-1].output.content_hash
                != self.resource_rows.video_file.processed_video_hash
            ):
                raise ValueError(
                    "Frame provenance must end at the transferred processed media"
                )
        recovery = (
            self.provenance.video_provenance_recovery if self.provenance else None
        )
        if recovery is not None:
            if (
                self.provenance is not None
                and self.provenance.video_frame_provenance is not None
            ):
                raise ValueError(
                    "Transfer must select verified ancestry or unresolved recovery"
                )
            if recovery.recording_hash != self.resource_hash or (
                recovery.processed_timeline.content_hash
                != self.resource_rows.video_file.processed_video_hash
            ):
                raise ValueError("Unresolved provenance belongs to different media")
        for segment in self.resource_rows.video_segments:
            if segment.source_node_key != self.source_node_key:
                raise ValueError("video segment source_node_key must match transfer")
            if segment.raw_video_hash != self.resource_hash:
                raise ValueError(
                    "video segment raw_video_hash must match resource_hash"
                )
            self._validate_segment_timeline(segment.timeline_coordinates)
        return self

    def _validate_segment_timeline(
        self, coordinates: VideoSegmentTimelineCoordinates
    ) -> None:
        """Bind segment ticks to the transferred processed timeline.

        Original-recording ticks depend on composed ancestry; receivers verify
        them by recomputing from the provenance bundle.
        """
        provenance = self.provenance
        if provenance is not None and provenance.video_frame_provenance is not None:
            processed = provenance.video_frame_provenance.transformations[-1].output
            expected_status = "verified"
        elif (
            provenance is not None and provenance.video_provenance_recovery is not None
        ):
            processed = provenance.video_provenance_recovery.processed_timeline
            expected_status = "unresolved"
        else:
            raise ValueError(
                "Video segments require frame provenance or an unresolved receipt"
            )
        if coordinates.recording_mapping_status != expected_status:
            raise ValueError(
                "Segment recording_mapping_status must match transferred provenance"
            )
        generation = coordinates.generation
        ticks = processed.presentation_timestamps
        if (
            generation.content_hash != processed.content_hash
            or (generation.time_base_num, generation.time_base_den)
            != (processed.time_base_num, processed.time_base_den)
            or generation.last_frame_number >= len(ticks)
            or ticks[generation.first_frame_number]
            != generation.first_presentation_timestamp
            or ticks[generation.last_frame_number]
            != generation.last_presentation_timestamp
        ):
            raise ValueError(
                "Segment generation coordinates disagree with the processed timeline"
            )
        if (
            coordinates.recording is not None
            and coordinates.recording.recording_content_hash != self.resource_hash
        ):
            raise ValueError(
                "Segment recording coordinates belong to another recording"
            )


class HubTransferReportTransferPayload(_HubTransferPayload):
    resource_kind: Literal["report"]
    resource_rows: HubTransferReportResourceRowsPayload


class HubTransferStudyResourceRowsPayload(_StrictPayload):
    study_exchange: StudyExchangeBundle

    @field_validator("study_exchange", mode="before")
    @classmethod
    def parse_exchange(cls, value: object) -> StudyExchangeBundle:
        from lx_dtypes.study_exchange import parse_study_exchange

        if isinstance(value, StudyExchangeBundle):
            return parse_study_exchange(value.model_dump_json())
        if isinstance(value, dict):
            return parse_study_exchange(json.dumps(value))
        raise ValueError("study_exchange must be a typed bundle or JSON object")

    @field_validator("study_exchange", mode="after")
    @classmethod
    def _require_pseudonyms(cls, value: StudyExchangeBundle) -> StudyExchangeBundle:
        for link in value.patients:
            require_hub_record_pseudonym(link.patient_uuid)
            require_hub_record_pseudonym(link.patient_examination_uuid)
        return value


class HubTransferStudyTransferPayload(_HubTransferPayload):
    """Standalone immutable study evidence; no media processing is requested."""

    resource_kind: Literal["study"] = "study"
    resource_rows: HubTransferStudyResourceRowsPayload
    transfer_mode: str = "metadata_only"
    processing_policy: str = "ingest_only_no_processing"
    processing_intent: str = "sender_requests_archive_only"
    cleanup_policy: str = "retain_all"
    transfer_key: str = Field(min_length=1, max_length=255)

    @model_validator(mode="after")
    def validate_study_identity(self) -> HubTransferStudyTransferPayload:
        from lx_dtypes.study_exchange import study_exchange_digest

        expected_policies = {
            "transfer_mode": "metadata_only",
            "processing_policy": "ingest_only_no_processing",
            "processing_intent": "sender_requests_archive_only",
            "cleanup_policy": "retain_all",
        }
        if any(
            getattr(self, name) != value for name, value in expected_policies.items()
        ):
            raise ValueError("Study transfers require metadata-only archival policies")
        digest = study_exchange_digest(self.resource_rows.study_exchange)
        if self.resource_hash != digest:
            raise ValueError("Study resource_hash must match canonical bundle digest")
        if self.transfer_key != f"{self.source_node_key}__study__{digest}__metadata_v1":
            raise ValueError("Study transfer_key must match source and bundle identity")
        if not self.processing_snapshot.sender_processing_success:
            raise ValueError("Study transfer requires validated sender metadata")
        return self


def validate_hub_transfer_study_payload(
    value: Mapping[str, JsonValue],
) -> HubTransferJsonObject:
    return _validate_payload(HubTransferStudyTransferPayload, value)


def _validate_payload(
    model_cls: type[BaseModel], value: Mapping[str, JsonValue]
) -> HubTransferJsonObject:
    if not isinstance(value, dict):
        raise TypeError("payload must be a JSON object")
    try:
        model = model_cls.model_validate(value)
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc
    return cast(HubTransferJsonObject, model.model_dump(mode="json", exclude_none=True))


def validate_hub_transfer_video_resource_rows(
    value: Mapping[str, JsonValue],
) -> HubTransferVideoResourceRowsData:
    return cast(
        HubTransferVideoResourceRowsData,
        _validate_payload(HubTransferVideoResourceRowsPayload, value),
    )


def validate_hub_transfer_report_resource_rows(
    value: Mapping[str, JsonValue],
) -> HubTransferReportResourceRowsData:
    return cast(
        HubTransferReportResourceRowsData,
        _validate_payload(HubTransferReportResourceRowsPayload, value),
    )


def validate_hub_transfer_processing_snapshot(
    value: Mapping[str, JsonValue],
) -> HubTransferProcessingSnapshotData:
    return cast(
        HubTransferProcessingSnapshotData,
        _validate_payload(HubTransferProcessingSnapshotPayload, value),
    )


def validate_hub_transfer_video_payload(
    value: Mapping[str, JsonValue],
) -> HubTransferVideoTransferPayloadData:
    return cast(
        HubTransferVideoTransferPayloadData,
        _validate_payload(HubTransferVideoTransferPayload, value),
    )


def validate_hub_transfer_report_payload(
    value: Mapping[str, JsonValue],
) -> HubTransferReportTransferPayloadData:
    return cast(
        HubTransferReportTransferPayloadData,
        _validate_payload(HubTransferReportTransferPayload, value),
    )


__all__ = [
    "HubTransferFrameAnnotationPayload",
    "HubTransferFrameAnnotationPayloadData",
    "HubTransferJsonObject",
    "HubTransferJsonScalar",
    "HubTransferJsonValue",
    "HubTransferProcessingHistoryPayload",
    "HubTransferProcessingHistoryPayloadData",
    "HubTransferProcessingSnapshotData",
    "HubTransferProcessingSnapshotPayload",
    "HubTransferProvenanceData",
    "HubTransferProvenancePayload",
    "HubTransferRawPdfFilePayload",
    "HubTransferRawPdfFilePayloadData",
    "HubTransferRawPdfStatePayload",
    "HubTransferRawPdfStatePayloadData",
    "HubTransferReportPayload",
    "HubTransferReportPayloadData",
    "HubTransferReportResourceRowsData",
    "HubTransferReportResourceRowsPayload",
    "HubTransferReportTransferPayload",
    "HubTransferReportTransferPayloadData",
    "HubTransferSegmentProvenancePayload",
    "HubTransferSegmentProvenancePayloadData",
    "HubTransferSegmentSourceKind",
    "HubTransferSegmentValidationState",
    "HubTransferSensitiveMetaPayload",
    "HubTransferSensitiveMetaPayloadData",
    "HubTransferStudyResourceRowsPayload",
    "HubTransferStudyTransferPayload",
    "HubTransferVideoFilePayload",
    "HubTransferVideoFilePayloadData",
    "HubTransferVideoResourceRowsData",
    "HubTransferVideoResourceRowsPayload",
    "HubTransferVideoSegmentPayload",
    "HubTransferVideoSegmentPayloadData",
    "HubTransferVideoStatePayload",
    "HubTransferVideoStatePayloadData",
    "HubTransferVideoTransferPayload",
    "HubTransferVideoTransferPayloadData",
    "validate_hub_transfer_processing_snapshot",
    "validate_hub_transfer_report_payload",
    "validate_hub_transfer_report_resource_rows",
    "validate_hub_transfer_study_payload",
    "validate_hub_transfer_video_payload",
    "validate_hub_transfer_video_resource_rows",
]
