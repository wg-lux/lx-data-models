from __future__ import annotations

from collections.abc import Mapping
from typing import TypeAlias, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .json_types import JsonObject, JsonValue

VideoAiJsonObject: TypeAlias = JsonObject


def _empty_label_list() -> list[VideoAiLabelPayload]:
    return []


def _empty_model_meta_list() -> list[VideoAiPredictionModelMetaPayload]:
    return []


def _empty_huggingface_model_list() -> list[VideoAiHuggingFaceModelPayload]:
    return []


def _strip_optional_text(value: str | int | float | bool | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip() or None
    return str(value).strip() or None


class VideoAiLabelPayload(BaseModel):
    """A minimal label reference returned by video AI endpoints."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: int = Field(ge=1)
    name: str = Field(min_length=1)


class VideoAiLabelSetPayload(BaseModel):
    """Label-set metadata returned by the video AI label-set list endpoint."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: int = Field(ge=1)
    name: str = Field(min_length=1)
    version: int
    description: str = ""
    label_count: int = Field(ge=0)
    labels: list[VideoAiLabelPayload] = Field(default_factory=_empty_label_list)


class VideoAiPredictionModelMetaPayload(BaseModel):
    """Locally registered prediction model metadata for video AI endpoints."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: int = Field(ge=1)
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    description: str = ""
    model_name: str = Field(min_length=1)
    ai_model_id: int = Field(ge=1)
    labelset_name: str = Field(min_length=1)
    labelset_version: int
    labelset_id: int = Field(ge=1)
    weights_available: bool
    is_active: bool


class VideoAiHuggingFaceModelPayload(BaseModel):
    """Known Hugging Face model option exposed by the prediction model list."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    model_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    labelset_name: str = Field(min_length=1)


class VideoAiPredictionModelListPayload(BaseModel):
    """Response payload for locally registered and materializable model choices."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    models: list[VideoAiPredictionModelMetaPayload] = Field(
        default_factory=_empty_model_meta_list
    )
    default_huggingface_model_id: str = Field(min_length=1)
    default_model_name: str = Field(min_length=1)
    default_labelset_name: str = Field(min_length=1)
    huggingface_models: list[VideoAiHuggingFaceModelPayload] = Field(
        default_factory=_empty_huggingface_model_list
    )


class VideoAiRerunPredictionRequestPayload(BaseModel):
    """Validated request payload for rerunning video prediction segments."""

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    model_meta_id: int | None = Field(default=None, ge=1)
    hf_model_id: str | None = None
    huggingface_model_id: str | None = None
    model_id: str | None = None
    labelset_name: str | None = None
    label_set_name: str | None = None
    labelset_version: int | str | None = None
    model_name: str | None = None
    model_meta_version: str | None = None
    replace_prediction_segments: bool = True
    delete_frames_after: bool = True
    ocr_frame_fraction: float = Field(default=0.001, ge=0)
    ocr_cap: int = Field(default=10, ge=0)
    test_run: bool = False
    n_test_frames: int = Field(default=10, ge=1)

    @field_validator(
        "hf_model_id",
        "huggingface_model_id",
        "model_id",
        "labelset_name",
        "label_set_name",
        "labelset_version",
        "model_name",
        "model_meta_version",
        mode="before",
    )
    @classmethod
    def _normalize_optional_text(
        cls, value: str | int | float | bool | None
    ) -> str | None:
        return _strip_optional_text(value)

    @field_validator(
        "replace_prediction_segments",
        "delete_frames_after",
        "test_run",
        mode="before",
    )
    @classmethod
    def _normalize_bool(cls, value: bool | str | int | None) -> bool | str | int | None:
        if value is None or isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "y", "on"}:
                return True
            if normalized in {"0", "false", "no", "n", "off"}:
                return False
        return value

    @property
    def resolved_huggingface_model_id(self) -> str | None:
        return self.hf_model_id or self.huggingface_model_id or self.model_id

    @property
    def resolved_labelset_name(self) -> str | None:
        return self.labelset_name or self.label_set_name

    def to_temporal_options_payload(self) -> VideoAiJsonObject:
        return cast(
            VideoAiJsonObject, self.model_dump(mode="python", exclude_none=True)
        )


class VideoAiPredictionJobPayload(BaseModel):
    """Job metadata returned after dispatching prediction reruns."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    task_id: str
    history_id: int | None = Field(default=None, ge=1)
    mode: str
    queue: str


class VideoAiRerunPredictionResponsePayload(BaseModel):
    """Response payload for the video prediction rerun endpoint."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    success: bool
    status: str = Field(min_length=1)
    queued: bool
    pending: bool
    video_id: int = Field(ge=1)
    model_meta: VideoAiPredictionModelMetaPayload
    job: VideoAiPredictionJobPayload
    deleted_prediction_segments: int | None = Field(default=None, ge=0)
    prediction_segments_count: int = Field(ge=0)
    reason: str | None = None
    message: str | None = None
    blocked_by_history_id: int | None = Field(default=None, ge=1)

    def to_response_dict(self) -> VideoAiJsonObject:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload["job"] = self.job.model_dump(mode="json", exclude_none=False)
        payload["deleted_prediction_segments"] = self.deleted_prediction_segments
        return cast(VideoAiJsonObject, payload)


class VideoAiLabelNamePayload(BaseModel):
    """Request payload for creating or deleting a label by name."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    name: str = Field(min_length=1)


class VideoAiLabelRenamePayload(BaseModel):
    """Request payload for renaming a label."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    name_old: str = Field(min_length=1)
    name: str = Field(min_length=1)


class VideoAiLabelMutationResponsePayload(BaseModel):
    """Response payload for label create, delete, and rename mutations."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    success: str = Field(min_length=1)
    id: int | None = Field(default=None, ge=1)
    name: str | None = Field(default=None, min_length=1)

    def to_response_dict(self) -> VideoAiJsonObject:
        return cast(VideoAiJsonObject, self.model_dump(mode="json", exclude_none=True))


def video_ai_json_safe_dict(payload: Mapping[str, JsonValue]) -> VideoAiJsonObject:
    if not isinstance(payload, Mapping):
        return {}
    mapping = cast(Mapping[object, object], payload)
    return {str(key): cast(JsonValue, value) for key, value in mapping.items()}


def validate_video_ai_rerun_prediction_request(
    payload: Mapping[str, JsonValue],
) -> VideoAiRerunPredictionRequestPayload:
    return VideoAiRerunPredictionRequestPayload.model_validate(
        video_ai_json_safe_dict(payload)
    )


def validate_video_ai_label_name_payload(
    payload: Mapping[str, JsonValue],
) -> VideoAiLabelNamePayload:
    return VideoAiLabelNamePayload.model_validate(video_ai_json_safe_dict(payload))


def validate_video_ai_label_rename_payload(
    payload: Mapping[str, JsonValue],
) -> VideoAiLabelRenamePayload:
    return VideoAiLabelRenamePayload.model_validate(video_ai_json_safe_dict(payload))


__all__ = [
    "VideoAiHuggingFaceModelPayload",
    "VideoAiJsonObject",
    "VideoAiLabelNamePayload",
    "VideoAiLabelMutationResponsePayload",
    "VideoAiLabelPayload",
    "VideoAiLabelRenamePayload",
    "VideoAiLabelSetPayload",
    "VideoAiPredictionJobPayload",
    "VideoAiPredictionModelListPayload",
    "VideoAiPredictionModelMetaPayload",
    "VideoAiRerunPredictionRequestPayload",
    "VideoAiRerunPredictionResponsePayload",
    "validate_video_ai_label_name_payload",
    "validate_video_ai_label_rename_payload",
    "validate_video_ai_rerun_prediction_request",
    "video_ai_json_safe_dict",
]
