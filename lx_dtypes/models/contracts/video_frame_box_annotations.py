from __future__ import annotations

from collections.abc import Mapping
from typing import TypeAlias, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .json_types import JsonNumericObject, JsonValue

VideoFrameBoxJsonObject: TypeAlias = JsonNumericObject


def _empty_annotation_list() -> list[VideoFrameBoxJsonObject]:
    return []


def _blank_to_none(value: object) -> object:
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip() or None
    return str(value).strip() or None


def _normalize_mapping(value: Mapping[object, object]) -> VideoFrameBoxJsonObject:
    return {str(key): cast(JsonValue, item) for key, item in value.items()}


class VideoFrameBoxAnnotationRequestPayload(BaseModel):
    """Top-level request wrapper for frame box annotation upserts."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    annotations: list[VideoFrameBoxJsonObject] = Field(
        default_factory=_empty_annotation_list
    )
    replace: bool = False
    video_id: int | None = Field(default=None, ge=1)
    frame_id: int | None = Field(default=None, ge=1)
    annotator: str | None = None
    information_source_name: str | None = None
    information_source: str | None = None

    @field_validator("replace", mode="before")
    @classmethod
    def _normalize_bool(cls, value: object) -> object:
        if value is None or isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "y", "on"}:
                return True
            if normalized in {"0", "false", "no", "n", "off"}:
                return False
        return value

    @field_validator("video_id", "frame_id", mode="before")
    @classmethod
    def _normalize_optional_int(cls, value: object) -> object:
        if value == "":
            return None
        return value

    @field_validator(
        "annotator",
        "information_source_name",
        "information_source",
        mode="before",
    )
    @classmethod
    def _normalize_optional_text(cls, value: object) -> object:
        return _blank_to_none(value)

    @field_validator("annotations", mode="before")
    @classmethod
    def _normalize_annotations(cls, value: object) -> object:
        if not isinstance(value, list):
            return value

        normalized: list[VideoFrameBoxJsonObject] = []
        for item in value:
            if not isinstance(item, Mapping):
                return value
            normalized.append(_normalize_mapping(item))
        return normalized

    @property
    def resolved_information_source_name(self) -> str | None:
        return self.information_source_name or self.information_source


class VideoFrameBoxAnnotationListResponsePayload(BaseModel):
    """Response payload for listing frame box annotations."""

    model_config = ConfigDict(extra="forbid")

    status: str = "success"
    frame_id: int = Field(ge=1)
    video_id: int = Field(ge=1)
    annotations: list[VideoFrameBoxJsonObject] = Field(
        default_factory=_empty_annotation_list
    )
    count: int = Field(ge=0)

    def to_response_dict(self) -> VideoFrameBoxJsonObject:
        return cast(VideoFrameBoxJsonObject, self.model_dump(mode="json"))


class VideoFrameBoxAnnotationMutationResponsePayload(BaseModel):
    """Response payload for frame box annotation upsert or delete operations."""

    model_config = ConfigDict(extra="forbid")

    status: str = "success"
    video_id: int | None = Field(default=None, ge=1)
    upserted_count: int = Field(ge=0)
    deleted_count: int | None = Field(default=None, ge=0)
    annotations: list[VideoFrameBoxJsonObject] = Field(
        default_factory=_empty_annotation_list
    )

    def to_response_dict(self) -> VideoFrameBoxJsonObject:
        return cast(
            VideoFrameBoxJsonObject,
            self.model_dump(mode="json", exclude_none=True),
        )


class VideoPhiRegionPayload(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True, str_strip_whitespace=True)

    x: float = Field(ge=0)
    y: float = Field(ge=0)
    width: float = Field(gt=0)
    height: float = Field(gt=0)
    source: str = "phi_detector"
    confidence: float | None = None


class VideoPhiFrameObservationPayload(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)

    frame_number: int | None = Field(default=None, ge=0)
    frame_id: int | None = Field(default=None, ge=0)
    image_width: int = Field(ge=1)
    image_height: int = Field(ge=1)
    phi_regions: list[VideoPhiRegionPayload] = Field(default_factory=list)

    @property
    def resolved_frame_number(self) -> int | None:
        return self.frame_number if self.frame_number is not None else self.frame_id


def validate_video_phi_frame_observations(
    payload: object,
) -> list[VideoPhiFrameObservationPayload]:
    if not isinstance(payload, list):
        return []
    observations: list[VideoPhiFrameObservationPayload] = []
    for item in payload:
        try:
            observations.append(VideoPhiFrameObservationPayload.model_validate(item))
        except ValueError:
            continue
    return observations


def video_frame_box_json_safe_dict(payload: object) -> VideoFrameBoxJsonObject:
    if not isinstance(payload, Mapping):
        return {}
    return _normalize_mapping(payload)


def validate_video_frame_box_annotation_request(
    payload: object,
) -> VideoFrameBoxAnnotationRequestPayload:
    if isinstance(payload, list):
        return VideoFrameBoxAnnotationRequestPayload.model_validate(
            {"annotations": payload}
        )
    return VideoFrameBoxAnnotationRequestPayload.model_validate(
        video_frame_box_json_safe_dict(payload)
    )


__all__ = [
    "VideoFrameBoxAnnotationListResponsePayload",
    "VideoFrameBoxAnnotationMutationResponsePayload",
    "VideoFrameBoxAnnotationRequestPayload",
    "VideoFrameBoxJsonObject",
    "VideoPhiFrameObservationPayload",
    "VideoPhiRegionPayload",
    "validate_video_phi_frame_observations",
    "validate_video_frame_box_annotation_request",
    "video_frame_box_json_safe_dict",
]
