from __future__ import annotations

from collections.abc import Mapping
from typing import Literal, NotRequired, TypedDict, cast

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from .json_types import JsonValue

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
    video_hash: str
    processed_video_hash: str
    suffix: str | None
    fps: float | None
    duration: float | None
    frame_count: int | None
    width: int | None
    height: int | None


class HubTransferSensitiveMetaPayloadData(TypedDict):
    patient_hash: str
    examination_hash: str


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
    video_hash: str
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
    video_hash: str
    start_frame_number: int
    end_frame_number_exclusive: int
    label_name: str
    source_kind: HubTransferSegmentSourceKind
    validation_state: HubTransferSegmentValidationState
    export_segment: bool
    anonymous_provenance: HubTransferSegmentProvenancePayloadData
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
    payload_schema_version: Literal["3.0"]
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
    payload_schema_version: Literal["3.0"]
    resource_rows: HubTransferReportResourceRowsData
    processing_snapshot: HubTransferProcessingSnapshotData
    provenance: NotRequired[HubTransferProvenanceData]


class _StrictPayload(BaseModel):
    model_config = ConfigDict(
        extra="forbid", frozen=True, strict=True, str_strip_whitespace=True
    )


class HubTransferVideoFilePayload(_StrictPayload):
    video_hash: str = Field(min_length=1)
    processed_video_hash: str = Field(min_length=1)
    suffix: str | None = None
    fps: float | None = Field(default=None, ge=0)
    duration: float | None = Field(default=None, ge=0)
    frame_count: int | None = Field(default=None, ge=0)
    width: int | None = Field(default=None, ge=1)
    height: int | None = Field(default=None, ge=1)


class HubTransferSensitiveMetaPayload(_StrictPayload):
    patient_hash: str = Field(min_length=1)
    examination_hash: str = Field(min_length=1)


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
    video_hash: str = Field(min_length=1)
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
    video_hash: str = Field(min_length=1)
    start_frame_number: int = Field(ge=0)
    end_frame_number_exclusive: int = Field(ge=1)
    label_name: str = Field(min_length=1)
    source_kind: HubTransferSegmentSourceKind
    validation_state: HubTransferSegmentValidationState
    export_segment: bool
    anonymous_provenance: HubTransferSegmentProvenancePayload
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
    payload_schema_version: Literal["3.0"]
    processing_snapshot: HubTransferProcessingSnapshotPayload
    provenance: HubTransferProvenancePayload | None = None


class HubTransferVideoTransferPayload(_HubTransferPayload):
    resource_kind: Literal["video"]
    resource_rows: HubTransferVideoResourceRowsPayload

    @model_validator(mode="after")
    def _validate_resource_linkage(self) -> HubTransferVideoTransferPayload:
        if self.resource_rows.video_file.video_hash != self.resource_hash:
            raise ValueError("video_file.video_hash must match resource_hash")
        for segment in self.resource_rows.video_segments:
            if segment.source_node_key != self.source_node_key:
                raise ValueError("video segment source_node_key must match transfer")
            if segment.video_hash != self.resource_hash:
                raise ValueError("video segment video_hash must match resource_hash")
        return self


class HubTransferReportTransferPayload(_HubTransferPayload):
    resource_kind: Literal["report"]
    resource_rows: HubTransferReportResourceRowsPayload


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
    "validate_hub_transfer_video_payload",
    "validate_hub_transfer_video_resource_rows",
]
