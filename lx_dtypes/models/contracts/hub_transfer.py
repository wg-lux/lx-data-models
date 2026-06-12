from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict, cast

from pydantic import BaseModel, ConfigDict, ValidationError

from .json_types import JsonValue

type HubTransferJsonScalar = str | int | float | bool | None
type HubTransferJsonValue = (
    HubTransferJsonScalar
    | list["HubTransferJsonValue"]
    | dict[str, "HubTransferJsonValue"]
)
type HubTransferJsonObject = dict[str, HubTransferJsonValue]


class HubTransferVideoFilePayloadData(TypedDict):
    video_hash: str
    original_file_name: str
    suffix: str
    fps: float
    duration: float
    frame_count: int
    width: int
    height: int
    meta: HubTransferJsonObject
    processed_video_hash: NotRequired[str]


class HubTransferSensitiveMetaPayloadData(TypedDict):
    patient_first_name: str
    patient_last_name: str
    patient_dob: str
    examination_date: str


class HubTransferVideoStatePayloadData(TypedDict):
    processing_started: bool
    frames_extracted: bool
    sensitive_meta_processed: bool
    frame_annotations_generated: NotRequired[bool]


class HubTransferProcessingHistoryPayloadData(TypedDict):
    file_hash: str
    success: bool


class HubTransferFrameAnnotationPayloadData(TypedDict):
    annotation_id: int
    video_hash: str
    frame_number: int
    frame_relative_path: str
    frame_timestamp: float
    label_name: str
    value: bool
    float_value: float
    annotator: str
    information_source_name: str


class HubTransferReportPayloadData(TypedDict):
    id: int
    patient_examination: int
    template_name: str
    template_version: str
    template_hash: str
    title: str
    status: str
    editor_payload: HubTransferJsonObject
    patient_context_snapshot: NotRequired[HubTransferJsonObject]
    history_context_snapshot: NotRequired[HubTransferJsonObject]
    rendered_text: str
    version: int
    is_active: bool
    finalized_at: NotRequired[str]


class HubTransferVideoResourceRowsData(TypedDict, total=False):
    video_file: HubTransferVideoFilePayloadData
    sensitive_meta: HubTransferSensitiveMetaPayloadData
    video_state: HubTransferVideoStatePayloadData
    processing_history: HubTransferProcessingHistoryPayloadData
    frame_annotations: list[HubTransferFrameAnnotationPayloadData]
    reports: list[HubTransferReportPayloadData]


class HubTransferRawPdfFilePayloadData(TypedDict):
    pdf_hash: str
    text: str


class HubTransferRawPdfStatePayloadData(TypedDict):
    processing_started: bool
    text_meta_extracted: bool
    sensitive_meta_processed: NotRequired[bool]


class HubTransferReportResourceRowsData(TypedDict, total=False):
    raw_pdf_file: HubTransferRawPdfFilePayloadData
    sensitive_meta: HubTransferSensitiveMetaPayloadData
    raw_pdf_state: HubTransferRawPdfStatePayloadData
    processing_history: HubTransferProcessingHistoryPayloadData
    reports: list[HubTransferReportPayloadData]


class HubTransferProcessingSnapshotData(TypedDict):
    sender_processing_success: bool


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
    resource_rows: HubTransferVideoResourceRowsData
    processing_snapshot: HubTransferProcessingSnapshotData


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
    resource_rows: HubTransferReportResourceRowsData
    processing_snapshot: HubTransferProcessingSnapshotData


class HubTransferVideoFilePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    video_hash: str
    original_file_name: str
    suffix: str
    fps: float
    duration: float
    frame_count: int
    width: int
    height: int
    meta: HubTransferJsonObject
    processed_video_hash: str | None = None


class HubTransferSensitiveMetaPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    patient_first_name: str
    patient_last_name: str
    patient_dob: str
    examination_date: str


class HubTransferVideoStatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    processing_started: bool
    frames_extracted: bool
    sensitive_meta_processed: bool
    frame_annotations_generated: bool | None = None


class HubTransferProcessingHistoryPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    file_hash: str
    success: bool


class HubTransferFrameAnnotationPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    annotation_id: int
    video_hash: str
    frame_number: int
    frame_relative_path: str
    frame_timestamp: float
    label_name: str
    value: bool
    float_value: float
    annotator: str
    information_source_name: str


class HubTransferReportPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    id: int
    patient_examination: int
    template_name: str
    template_version: str
    template_hash: str
    title: str
    status: str
    editor_payload: HubTransferJsonObject
    patient_context_snapshot: HubTransferJsonObject | None = None
    history_context_snapshot: HubTransferJsonObject | None = None
    rendered_text: str
    version: int
    is_active: bool
    finalized_at: str | None = None


class HubTransferVideoResourceRowsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    video_file: HubTransferVideoFilePayload
    sensitive_meta: HubTransferSensitiveMetaPayload
    video_state: HubTransferVideoStatePayload
    processing_history: HubTransferProcessingHistoryPayload
    frame_annotations: list[HubTransferFrameAnnotationPayload] | None = None
    reports: list[HubTransferReportPayload] | None = None


class HubTransferRawPdfFilePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    pdf_hash: str
    text: str


class HubTransferRawPdfStatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    processing_started: bool
    text_meta_extracted: bool
    sensitive_meta_processed: bool | None = None


class HubTransferReportResourceRowsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    raw_pdf_file: HubTransferRawPdfFilePayload
    sensitive_meta: HubTransferSensitiveMetaPayload
    raw_pdf_state: HubTransferRawPdfStatePayload
    processing_history: HubTransferProcessingHistoryPayload
    reports: list[HubTransferReportPayload] | None = None


class HubTransferProcessingSnapshotPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    sender_processing_success: bool


class HubTransferVideoTransferPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

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
    resource_rows: HubTransferVideoResourceRowsPayload
    processing_snapshot: HubTransferProcessingSnapshotPayload


class HubTransferReportTransferPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

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
    resource_rows: HubTransferReportResourceRowsPayload
    processing_snapshot: HubTransferProcessingSnapshotPayload


def _validate_payload(
    model_cls: type[BaseModel],
    value: Any,
) -> dict[str, JsonValue]:
    if not isinstance(value, dict):
        raise ValueError("payload must be a JSON object")
    try:
        model = model_cls.model_validate(value)
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc
    return cast(dict[str, JsonValue], model.model_dump(mode="json", exclude_none=True))


def validate_hub_transfer_video_resource_rows(
    value: Any,
) -> HubTransferVideoResourceRowsData:
    return cast(
        HubTransferVideoResourceRowsData,
        _validate_payload(HubTransferVideoResourceRowsPayload, value),
    )


def validate_hub_transfer_report_resource_rows(
    value: Any,
) -> HubTransferReportResourceRowsData:
    return cast(
        HubTransferReportResourceRowsData,
        _validate_payload(HubTransferReportResourceRowsPayload, value),
    )


def validate_hub_transfer_processing_snapshot(
    value: Any,
) -> HubTransferProcessingSnapshotData:
    return cast(
        HubTransferProcessingSnapshotData,
        _validate_payload(HubTransferProcessingSnapshotPayload, value),
    )


def validate_hub_transfer_video_payload(
    value: Any,
) -> HubTransferVideoTransferPayloadData:
    return cast(
        HubTransferVideoTransferPayloadData,
        _validate_payload(HubTransferVideoTransferPayload, value),
    )


def validate_hub_transfer_report_payload(
    value: Any,
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
    "HubTransferSensitiveMetaPayload",
    "HubTransferSensitiveMetaPayloadData",
    "HubTransferVideoFilePayload",
    "HubTransferVideoFilePayloadData",
    "HubTransferVideoResourceRowsData",
    "HubTransferVideoResourceRowsPayload",
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
