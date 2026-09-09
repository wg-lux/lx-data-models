from __future__ import annotations

from collections.abc import Mapping
from typing import Literal, TypedDict, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .json_types import JsonObject as BaseJsonObject
from .json_types import JsonValue as BaseJsonValue

type VideoReimportOperation = Literal["video_reimport"]
type VideoReimportDispatchStatus = Literal[
    "queued",
    "already_queued",
    "busy",
    "completed",
    "failed",
    "lost",
]
type VideoReimportStatus = VideoReimportDispatchStatus
type VideoReimportApiStatus = Literal[
    "queued",
    "already_queued",
    "busy",
    "completed",
    "failed",
    "lost",
    "done",
]
type VideoReimportErrorType = Literal[
    "integrity_lost",
    "missing_source",
    "dispatch_error",
    "media_busy",
    "processing_error",
    "storage_error",
    "validation_error",
]
type VideoReimportJobMode = Literal["celery", "inline"]
type VideoReimportPredictionRefreshStatus = Literal[
    "skipped",
    "not_queued",
    "failed",
]
type VideoReimportJsonValue = BaseJsonValue
type JsonValue = VideoReimportJsonValue
type JsonObject = BaseJsonObject
type VideoReimportRequestData = JsonObject

VIDEO_REIMPORT_OPERATION: VideoReimportOperation = "video_reimport"
VIDEO_REIMPORT_HISTORY_KIND: VideoReimportOperation = VIDEO_REIMPORT_OPERATION


def _empty_json_object() -> JsonObject:
    return {}


class VideoReimportRequestPayload(BaseModel):
    """Validated request payload for video re-import endpoints."""

    model_config = ConfigDict(extra="allow", str_strip_whitespace=True)

    refresh_predictions: bool | None = None
    model_meta_id: int | None = Field(default=None, ge=1)
    model_name: str | None = None
    model_meta_version: str | None = None
    test_run: bool | None = None
    n_test_frames: int | None = Field(default=None, ge=1)
    delete_frames_after: bool | None = None

    @field_validator(
        "refresh_predictions",
        "test_run",
        "delete_frames_after",
        mode="before",
    )
    @classmethod
    def _normalize_optional_bool(
        cls, value: bool | str | int | None
    ) -> bool | str | int | None:
        if value is None or isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "y", "on"}:
                return True
            if normalized in {"0", "false", "no", "n", "off"}:
                return False
        return value

    @field_validator("model_name", "model_meta_version", mode="before")
    @classmethod
    def _blank_to_none(cls, value: str | float | bool | None) -> str | None:
        if isinstance(value, str):
            return value.strip() or None
        if value is None:
            return None
        return str(value)

    def to_payload_dict(self) -> JsonObject:
        return cast(
            JsonObject,
            self.model_dump(mode="json", exclude_none=True, exclude_unset=True),
        )


class VideoReimportHistoryConfig(BaseModel):
    """Persisted processing-history config for a video re-import job."""

    model_config = ConfigDict(extra="forbid")

    kind: VideoReimportOperation = VIDEO_REIMPORT_OPERATION
    queue: str = Field(min_length=1)
    refresh_predictions: bool = True
    prediction_payload: JsonObject = Field(default_factory=_empty_json_object)


class VideoReimportDispatchResult(BaseModel):
    """Queue or inline execution result returned by video re-import dispatch."""

    model_config = ConfigDict(extra="forbid")

    task_id: str
    mode: VideoReimportJobMode
    status: VideoReimportDispatchStatus
    operation: VideoReimportOperation = VIDEO_REIMPORT_HISTORY_KIND
    video_id: int = Field(ge=1)
    queue: str = Field(min_length=1)
    history_id: int | None = Field(default=None, ge=1)
    poll_url: str | None = None
    message: str | None = None
    reason: str | None = None
    prediction_refresh: JsonObject | None = None

    def to_dict(self) -> JsonObject:
        return cast(JsonObject, self.model_dump(mode="json", exclude_none=True))


class VideoReimportPredictionRefreshPayload(BaseModel):
    """Fallback prediction-refresh status produced after inline re-import."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    status: VideoReimportPredictionRefreshStatus
    queued: bool = False
    reason: str | None = None
    error: str | None = None

    def to_dict(self) -> JsonObject:
        return cast(JsonObject, self.model_dump(mode="json", exclude_none=True))


class VideoReimportApiResponseData(TypedDict, total=False):
    error: str
    error_type: VideoReimportErrorType
    message: str
    status: VideoReimportApiStatus
    operation: VideoReimportOperation
    reason: str
    video_id: int
    uuid: str
    updated_in_place: bool
    task_id: str
    mode: str
    queue: str
    history_id: int
    poll_url: str
    frame_cleaning_applied: bool
    sensitive_meta_created: bool
    sensitive_meta_id: int | None
    reset_upload_jobs: int
    completed_upload_jobs: int
    prediction_refresh: JsonObject


class VideoReimportApiResponsePayload(BaseModel):
    """Validated API response payload for video re-import endpoints."""

    model_config = ConfigDict(extra="allow", str_strip_whitespace=True)

    error: str | None = None
    error_type: VideoReimportErrorType | None = None
    message: str | None = None
    status: VideoReimportApiStatus | None = None
    operation: VideoReimportOperation | None = None
    reason: str | None = None
    video_id: int | None = Field(default=None, ge=1)
    uuid: str | None = None
    updated_in_place: bool | None = None
    task_id: str | None = None
    mode: VideoReimportJobMode | None = None
    queue: str | None = Field(default=None, min_length=1)
    history_id: int | None = Field(default=None, ge=1)
    poll_url: str | None = None
    frame_cleaning_applied: bool | None = None
    sensitive_meta_created: bool | None = None
    sensitive_meta_id: int | None = Field(default=None, ge=1)
    reset_upload_jobs: int | None = Field(default=None, ge=0)
    completed_upload_jobs: int | None = Field(default=None, ge=0)
    prediction_refresh: JsonObject | None = None


def video_reimport_json_safe(value: object) -> VideoReimportJsonValue:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        mapping = cast(Mapping[object, object], value)
        return cast(
            VideoReimportJsonValue,
            {str(key): video_reimport_json_safe(item) for key, item in mapping.items()},
        )
    if isinstance(value, (list, tuple)):
        items = cast(list[object] | tuple[object, ...], value)
        return cast(
            VideoReimportJsonValue,
            [video_reimport_json_safe(item) for item in items],
        )
    return str(value)


def video_reimport_json_safe_dict(payload: Mapping[str, JsonValue]) -> JsonObject:
    mapping = cast(Mapping[object, object], payload)
    return cast(
        JsonObject,
        {str(key): video_reimport_json_safe(value) for key, value in mapping.items()},
    )


def validate_video_reimport_request_payload(
    payload: Mapping[str, JsonValue],
) -> VideoReimportRequestPayload:
    return VideoReimportRequestPayload.model_validate(
        video_reimport_json_safe_dict(payload)
    )


def dump_video_reimport_request_payload(
    payload: VideoReimportRequestPayload,
) -> VideoReimportRequestData:
    return payload.to_payload_dict()


def dump_video_reimport_api_response(
    payload: VideoReimportApiResponsePayload,
) -> VideoReimportApiResponseData:
    return cast(
        VideoReimportApiResponseData,
        payload.model_dump(mode="json", exclude_none=True),
    )


__all__ = [
    "VIDEO_REIMPORT_HISTORY_KIND",
    "VIDEO_REIMPORT_OPERATION",
    "JsonObject",
    "JsonValue",
    "VideoReimportApiResponseData",
    "VideoReimportApiResponsePayload",
    "VideoReimportApiStatus",
    "VideoReimportDispatchResult",
    "VideoReimportDispatchStatus",
    "VideoReimportErrorType",
    "VideoReimportHistoryConfig",
    "VideoReimportJobMode",
    "VideoReimportJsonValue",
    "VideoReimportOperation",
    "VideoReimportPredictionRefreshPayload",
    "VideoReimportPredictionRefreshStatus",
    "VideoReimportRequestData",
    "VideoReimportRequestPayload",
    "VideoReimportStatus",
    "dump_video_reimport_api_response",
    "dump_video_reimport_request_payload",
    "validate_video_reimport_request_payload",
    "video_reimport_json_safe",
    "video_reimport_json_safe_dict",
]
