from __future__ import annotations

from collections.abc import Mapping
from typing import Literal, TypedDict, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .json_types import JsonObject, JsonValue

type VideoCorrectionMaskType = Literal["device", "custom"]
type VideoCorrectionProcessingMethod = Literal["streaming", "direct", "traditional"]


class VideoCorrectionRoiData(TypedDict, total=False):
    x: float
    y: float
    width: float
    height: float
    image_width: float | None
    image_height: float | None


class VideoCorrectionSegmentUpdateData(TypedDict):
    segments_updated: int
    segments_deleted: int
    segments_unchanged: int


class VideoCorrectionRoiPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    x: float = Field(ge=0)
    y: float = Field(ge=0)
    width: float = Field(ge=0)
    height: float = Field(ge=0)
    image_width: float | None = Field(default=None, ge=0)
    image_height: float | None = Field(default=None, ge=0)

    @model_validator(mode="before")
    @classmethod
    def normalize_endoscope_roi_aliases(
        cls, value: Mapping[str, JsonValue] | VideoCorrectionRoiPayload
    ) -> Mapping[str, JsonValue] | VideoCorrectionRoiPayload:
        if not isinstance(value, Mapping):
            return value
        data = dict(value)
        if {"x", "y", "width", "height"}.issubset(data):
            return data
        if {
            "endoscope_x",
            "endoscope_y",
            "endoscope_width",
            "endoscope_height",
        }.issubset(data):
            return {
                "x": data.get("endoscope_x"),
                "y": data.get("endoscope_y"),
                "width": data.get("endoscope_width"),
                "height": data.get("endoscope_height"),
                "image_width": data.get("image_width"),
                "image_height": data.get("image_height"),
            }
        return data


def _blank_to_none(value: str | float | bool | None) -> str | None:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    if value is None:
        return None
    return str(value).strip() or None


def _payload_dict(payload: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    return dict(payload)


def _coerce_payload_bool(value: bool | str | int | None) -> bool | None:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _normalize_optional_int_list(
    value: list[int] | tuple[int, ...] | int | str | None,
) -> list[int] | None:
    if value is None:
        return None
    if isinstance(value, list):
        return [
            cast(int, item) for item in cast(list[object], value) if item is not None
        ]
    return [cast(int, value)]


class VideoCorrectionProcessingMethodMixin(BaseModel):
    processing_method: VideoCorrectionProcessingMethod | None = None
    use_streaming: bool | None = None

    @field_validator("use_streaming", mode="before")
    @classmethod
    def normalize_use_streaming(cls, value: bool | str | int | None) -> bool | None:
        return _coerce_payload_bool(value)

    @property
    def resolved_processing_method(self) -> VideoCorrectionProcessingMethod:
        if self.processing_method is not None:
            return self.processing_method
        if self.use_streaming is None:
            return "streaming"
        return "streaming" if self.use_streaming else "direct"


class VideoCorrectionApplyMaskPayload(VideoCorrectionProcessingMethodMixin):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    mask_type: VideoCorrectionMaskType = "device"
    device_name: str | None = None
    roi: VideoCorrectionRoiPayload | None = None
    custom_mask: VideoCorrectionRoiPayload | None = None

    @field_validator("device_name", mode="before")
    @classmethod
    def normalize_device_name(cls, value: str | float | bool | None) -> str | None:
        return _blank_to_none(value)

    @model_validator(mode="after")
    def validate_mask_payload(self) -> VideoCorrectionApplyMaskPayload:
        if self.mask_type == "device" and not self.device_name:
            raise ValueError("device_name required for device mask")
        if self.mask_type == "custom" and self.resolved_roi is None:
            raise ValueError("roi required for custom mask")
        return self

    @property
    def resolved_roi(self) -> VideoCorrectionRoiPayload | None:
        return self.roi or self.custom_mask

    def history_config(self) -> JsonObject:
        roi = self.resolved_roi
        config: JsonObject = {
            "mask_type": self.mask_type,
            "processing_method": self.resolved_processing_method,
        }
        if self.device_name is not None:
            config["device_name"] = self.device_name
        if roi is not None:
            config["roi"] = cast(JsonValue, dump_video_correction_roi_payload(roi))
        return config


class VideoCorrectionFrameRemovalPayload(VideoCorrectionProcessingMethodMixin):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    frame_list: list[int] | None = None
    manual_frames: list[int] | None = None
    frame_ranges: str | None = None
    detection_method: str | None = None
    selection_method: str | None = None

    @field_validator("frame_list", "manual_frames", mode="before")
    @classmethod
    def normalize_frame_list(
        cls, value: list[int] | tuple[int, ...] | int | str | None
    ) -> list[int] | None:
        return _normalize_optional_int_list(value)

    @field_validator(
        "frame_ranges", "detection_method", "selection_method", mode="before"
    )
    @classmethod
    def normalize_optional_text(cls, value: str | float | bool | None) -> str | None:
        return _blank_to_none(value)

    @model_validator(mode="after")
    def validate_frame_selection(self) -> VideoCorrectionFrameRemovalPayload:
        if self.frame_list is not None and any(frame < 0 for frame in self.frame_list):
            raise ValueError("frame_list must contain non-negative integers")
        if self.manual_frames is not None and any(
            frame < 0 for frame in self.manual_frames
        ):
            raise ValueError("manual_frames must contain non-negative integers")
        if self.frame_ranges:
            parse_video_correction_frame_ranges(self.frame_ranges)
        return self

    @property
    def resolved_detection_method(self) -> str | None:
        if self.detection_method is not None:
            return self.detection_method
        if self.selection_method == "automatic":
            return "automatic"
        return None

    def explicit_frames(self) -> list[int] | None:
        if self.frame_list is not None:
            return self.frame_list
        if self.manual_frames is not None:
            return self.manual_frames
        if self.frame_ranges:
            return parse_video_correction_frame_ranges(self.frame_ranges)
        return None


class VideoCorrectionSegmentUpdatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    segments_updated: int = Field(ge=0)
    segments_deleted: int = Field(ge=0)
    segments_unchanged: int = Field(ge=0)


class VideoCorrectionErrorPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    error: str = Field(min_length=1)


class VideoCorrectionApplyMaskResponsePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    task_id: str | None = None
    output_file: str = Field(min_length=1)
    message: str = Field(min_length=1)
    processing_time: float = Field(ge=0)


class VideoCorrectionRemoveFramesResponsePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    task_id: str | None = None
    output_file: str = Field(min_length=1)
    frames_removed: int = Field(ge=0)
    segment_updates: VideoCorrectionSegmentUpdatePayload
    message: str = Field(min_length=1)
    processing_time: float = Field(ge=0)


def parse_video_correction_frame_ranges(ranges_str: str) -> list[int]:
    frames: list[int] = []
    for part in ranges_str.split(","):
        normalized_part = part.strip()
        if not normalized_part:
            continue
        if "-" in normalized_part:
            start_text, end_text = normalized_part.split("-", maxsplit=1)
            start = int(start_text)
            end = int(end_text)
            if start < 0 or end < 0:
                raise ValueError("frame ranges must be non-negative")
            if end < start:
                raise ValueError(
                    "frame range end must be greater than or equal to start"
                )
            frames.extend(range(start, end + 1))
        else:
            frame = int(normalized_part)
            if frame < 0:
                raise ValueError("frame ranges must be non-negative")
            frames.append(frame)
    return sorted(set(frames))


def dump_video_correction_roi_payload(
    payload: VideoCorrectionRoiPayload,
) -> VideoCorrectionRoiData:
    return cast(
        VideoCorrectionRoiData,
        payload.model_dump(mode="python", exclude_none=True),
    )


def dump_video_correction_segment_update_payload(
    payload: VideoCorrectionSegmentUpdatePayload,
) -> VideoCorrectionSegmentUpdateData:
    return cast(VideoCorrectionSegmentUpdateData, payload.model_dump(mode="python"))


def validate_video_correction_apply_mask_payload(
    payload: Mapping[str, JsonValue],
) -> VideoCorrectionApplyMaskPayload:
    return VideoCorrectionApplyMaskPayload.model_validate(_payload_dict(payload))


def validate_video_correction_frame_removal_payload(
    payload: Mapping[str, JsonValue],
) -> VideoCorrectionFrameRemovalPayload:
    return VideoCorrectionFrameRemovalPayload.model_validate(_payload_dict(payload))


__all__ = [
    "VideoCorrectionApplyMaskPayload",
    "VideoCorrectionApplyMaskResponsePayload",
    "VideoCorrectionErrorPayload",
    "VideoCorrectionFrameRemovalPayload",
    "VideoCorrectionMaskType",
    "VideoCorrectionProcessingMethod",
    "VideoCorrectionRemoveFramesResponsePayload",
    "VideoCorrectionRoiData",
    "VideoCorrectionRoiPayload",
    "VideoCorrectionSegmentUpdateData",
    "VideoCorrectionSegmentUpdatePayload",
    "dump_video_correction_roi_payload",
    "dump_video_correction_segment_update_payload",
    "parse_video_correction_frame_ranges",
    "validate_video_correction_apply_mask_payload",
    "validate_video_correction_frame_removal_payload",
]
