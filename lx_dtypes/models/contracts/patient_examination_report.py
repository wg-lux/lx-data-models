from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime
from typing import Literal, NotRequired, TypeAlias, TypedDict, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .json_types import JsonObject, JsonValue

ReportJsonValue: TypeAlias = JsonValue
ReportJsonObject: TypeAlias = JsonObject
ReportStatus: TypeAlias = Literal["draft", "final"]
SegmentFrameSelectionAction: TypeAlias = Literal["set", "clear", "random", "step"]


class PatientReportIdentityData(TypedDict):
    first_name: str
    last_name: str
    dob: date


class PatientExaminationReportSubmissionData(TypedDict):
    patient_examination_id: int
    template_name: str
    template_version: str
    template_hash: str
    title: str
    status: ReportStatus
    rendered_text: str
    editor_payload: ReportJsonObject
    patient_data: ReportJsonObject
    indications: list[ReportJsonObject]
    findings: list[ReportJsonObject]
    history_limit: int
    report_id: NotRequired[int]
    expected_version: NotRequired[int]


class PatientExaminationReportMakeReportData(TypedDict):
    patient_examination_id: int
    patient: PatientReportIdentityData
    max_frames: int
    report_id: NotRequired[int]


class ReportPersistedArtifactsData(TypedDict):
    full_report_id: int | None
    pdf_id: int | None
    pdf_view_url: str | None
    pdf_download_url: str | None
    patient_timeline_url: str | None


class ReportSegmentFrameSelectionData(TypedDict, total=False):
    segment_id: int
    video_id: int
    frame_number: int
    frame_id: int | None
    relative_path: str | None
    finding_id: int | None
    patient_finding_id: int | None
    updated_at: str
    selection_source: str


ReportSegmentSelectionMap: TypeAlias = dict[str, ReportSegmentFrameSelectionData]


class SegmentFramePreviewData(TypedDict):
    frame_id: int
    frame_number: int
    timestamp: float | None
    relative_path: str
    file_exists: bool
    stream_url: str


class SegmentFrameControlsData(TypedDict):
    random_frame_number: int
    step_backward_5_frame_number: int
    step_forward_5_frame_number: int


class SegmentAttachedFindingData(TypedDict):
    patient_finding_id: int
    finding_id: int | None
    finding_name: str | None


class SegmentSelectionMetaData(TypedDict):
    updated_at: str | None
    selection_source: str | None


class SegmentFrameSelectorItemData(TypedDict):
    segment_id: int
    video_id: int
    label_id: int | None
    label_name: str | None
    start_frame_number: int
    end_frame_number: int
    segment_duration_seconds: float | None
    selected_frame_number: int | None
    selected_frame: SegmentFramePreviewData | None
    controls: SegmentFrameControlsData
    attached_finding: SegmentAttachedFindingData | None
    selection_meta: SegmentSelectionMetaData


class SegmentFrameSelectorResponseData(TypedDict):
    patient_examination_id: int
    report_id: int
    report_status: str
    report_template_name: str
    auto_created_report: bool
    storage_key: str
    count: int
    results: list[SegmentFrameSelectorItemData]


class ReportExportFrameDetailData(TypedDict):
    segment_id: int
    video_id: int
    frame_id: int
    frame_number: int
    label_name: str | None
    finding_name: str | None
    stream_url: str
    caption: str


class SegmentFrameSelectorQueryData(TypedDict, total=False):
    patient_examination_id: int
    report_id: int | None


class SegmentFrameSelectorPatchData(SegmentFrameSelectorQueryData, total=False):
    segment_id: int
    action: SegmentFrameSelectionAction
    frame_number: int | None
    step: int
    finding_id: int | None
    template_name: str | None


class PatientReportIdentityPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    first_name: str = Field(min_length=1, max_length=150)
    last_name: str = Field(min_length=1, max_length=150)
    dob: date


class PatientExaminationReportSubmissionPayload(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    report_id: int | None = Field(default=None, ge=1)
    patient_examination_id: int = Field(ge=1)
    template_name: str = Field(min_length=1)
    template_version: str = ""
    template_hash: str = ""
    title: str = ""
    status: ReportStatus = "draft"
    rendered_text: str = ""
    editor_payload: ReportJsonObject = Field(default_factory=dict)
    patient_data: ReportJsonObject = Field(default_factory=dict)
    indications: list[ReportJsonObject] = Field(default_factory=list)
    findings: list[ReportJsonObject] = Field(default_factory=list)
    expected_version: int | None = Field(default=None, ge=1)
    history_limit: int = Field(default=5, ge=1, le=50)


class PatientExaminationReportMakeReportPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    patient_examination_id: int = Field(ge=1)
    report_id: int | None = Field(default=None, ge=1)
    patient: PatientReportIdentityPayload
    max_frames: int = Field(default=12, ge=1, le=24)


class ReportPersistedArtifactsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_report_id: int | None = Field(default=None, ge=1)
    pdf_id: int | None = Field(default=None, ge=1)
    pdf_view_url: str | None = None
    pdf_download_url: str | None = None
    patient_timeline_url: str | None = None


class ReportSegmentFrameSelectionPayload(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    segment_id: int | None = Field(default=None, ge=1)
    video_id: int | None = Field(default=None, ge=1)
    frame_number: int | None = Field(default=None, ge=0)
    frame_id: int | None = Field(default=None, ge=1)
    relative_path: str | None = None
    finding_id: int | None = Field(default=None, ge=1)
    patient_finding_id: int | None = Field(default=None, ge=1)
    updated_at: str | None = None
    selection_source: str | None = None

    @field_validator("relative_path", "updated_at", "selection_source", mode="before")
    @classmethod
    def blank_to_none(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip() or None
        return value


class SegmentFrameSelectorQueryPayload(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    patient_examination_id: int = Field(ge=1)
    report_id: int | None = Field(default=None, ge=1)

    @field_validator("patient_examination_id", "report_id", mode="before")
    @classmethod
    def normalize_optional_id(cls, value: object) -> object:
        if value == "":
            return None
        return value


class SegmentFrameSelectorPatchPayload(SegmentFrameSelectorQueryPayload):
    segment_id: int = Field(ge=1)
    action: SegmentFrameSelectionAction = "set"
    frame_number: int | None = Field(default=None, ge=0)
    step: int = 5
    finding_id: int | None = Field(default=None, ge=1)
    template_name: str | None = None

    @field_validator("action", mode="before")
    @classmethod
    def normalize_action(cls, value: object) -> str:
        return str(value or "set").strip().lower()

    @field_validator("frame_number", "finding_id", "template_name", mode="before")
    @classmethod
    def normalize_blank_optional(cls, value: object) -> object:
        if value == "":
            return None
        if isinstance(value, str) and not value.strip():
            return None
        return value


def report_json_safe(value: object) -> ReportJsonValue:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        mapping = cast(Mapping[object, object], value)
        return {str(key): report_json_safe(item) for key, item in mapping.items()}
    if isinstance(value, (list, tuple)):
        items = cast(list[object] | tuple[object, ...], value)
        return [report_json_safe(item) for item in items]
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


def report_json_safe_dict(payload: object) -> ReportJsonObject:
    if not isinstance(payload, Mapping):
        return {}
    mapping = cast(Mapping[object, object], payload)
    return {str(key): report_json_safe(value) for key, value in mapping.items()}


def dump_report_submission_payload(
    payload: PatientExaminationReportSubmissionPayload,
) -> PatientExaminationReportSubmissionData:
    return cast(
        PatientExaminationReportSubmissionData,
        payload.model_dump(mode="python", exclude_none=True),
    )


def dump_make_report_payload(
    payload: PatientExaminationReportMakeReportPayload,
) -> PatientExaminationReportMakeReportData:
    return cast(
        PatientExaminationReportMakeReportData,
        payload.model_dump(mode="python", exclude_none=True),
    )


def dump_persisted_artifacts_payload(
    payload: ReportPersistedArtifactsPayload,
) -> ReportPersistedArtifactsData:
    return cast(ReportPersistedArtifactsData, payload.model_dump(mode="json"))


def dump_segment_frame_selection_payload(
    payload: ReportSegmentFrameSelectionPayload,
) -> ReportSegmentFrameSelectionData:
    return cast(
        ReportSegmentFrameSelectionData,
        payload.model_dump(mode="json", exclude_none=True),
    )


def validate_segment_selection_map(payload: object) -> ReportSegmentSelectionMap:
    if not isinstance(payload, Mapping):
        return {}
    result: ReportSegmentSelectionMap = {}
    selection_map = cast(Mapping[object, object], payload)
    for key, value in selection_map.items():
        if not isinstance(value, Mapping):
            continue
        selection = cast(Mapping[str, object], value)
        result[str(key)] = dump_segment_frame_selection_payload(
            ReportSegmentFrameSelectionPayload.model_validate(dict(selection))
        )
    return result


def dump_selector_query_payload(
    payload: SegmentFrameSelectorQueryPayload,
) -> SegmentFrameSelectorQueryData:
    return cast(
        SegmentFrameSelectorQueryData,
        payload.model_dump(mode="python", exclude_none=True),
    )


def dump_selector_patch_payload(
    payload: SegmentFrameSelectorPatchPayload,
) -> SegmentFrameSelectorPatchData:
    return cast(
        SegmentFrameSelectorPatchData,
        payload.model_dump(mode="python", exclude_none=True),
    )


__all__ = [
    "PatientExaminationReportMakeReportData",
    "PatientExaminationReportMakeReportPayload",
    "PatientExaminationReportSubmissionData",
    "PatientExaminationReportSubmissionPayload",
    "PatientReportIdentityData",
    "PatientReportIdentityPayload",
    "ReportExportFrameDetailData",
    "ReportJsonObject",
    "ReportJsonValue",
    "ReportPersistedArtifactsData",
    "ReportPersistedArtifactsPayload",
    "ReportSegmentFrameSelectionData",
    "ReportSegmentFrameSelectionPayload",
    "ReportSegmentSelectionMap",
    "ReportStatus",
    "SegmentAttachedFindingData",
    "SegmentFrameControlsData",
    "SegmentFramePreviewData",
    "SegmentFrameSelectionAction",
    "SegmentFrameSelectorItemData",
    "SegmentFrameSelectorPatchData",
    "SegmentFrameSelectorPatchPayload",
    "SegmentFrameSelectorQueryData",
    "SegmentFrameSelectorQueryPayload",
    "SegmentFrameSelectorResponseData",
    "SegmentSelectionMetaData",
    "dump_make_report_payload",
    "dump_persisted_artifacts_payload",
    "dump_report_submission_payload",
    "dump_segment_frame_selection_payload",
    "dump_selector_patch_payload",
    "dump_selector_query_payload",
    "report_json_safe",
    "report_json_safe_dict",
    "validate_segment_selection_map",
]
