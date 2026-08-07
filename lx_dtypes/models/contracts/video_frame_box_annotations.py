from __future__ import annotations

from collections.abc import Mapping
from typing import TypeAlias, cast

from pydantic import BaseModel, ConfigDict, Field

from .json_types import JsonNumericObject, JsonObject, JsonScalar, JsonValue
from .video_frame_annotations import FrameBoxAnnotationBulkEnvelopePayload

VideoFrameBoxJsonObject: TypeAlias = JsonNumericObject


def _empty_annotation_list() -> list[VideoFrameBoxJsonObject]:
    return []


def _normalize_mapping(
    value: Mapping[object, JsonValue],
) -> VideoFrameBoxJsonObject:
    return {str(key): _normalize_scalar(item) for key, item in value.items()}


def _normalize_scalar(value: JsonValue) -> JsonScalar:
    if isinstance(value, (str, int, float, bool)):
        return value
    return ""


VideoFrameBoxAnnotationRequestPayload = FrameBoxAnnotationBulkEnvelopePayload


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
    if payload is None:
        return []
    if not isinstance(payload, list):
        raise ValueError("frame_observations must be a list")
    observations: list[VideoPhiFrameObservationPayload] = []
    for item in payload:
        observations.append(VideoPhiFrameObservationPayload.model_validate(item))
    return observations


def video_frame_box_json_safe_dict(
    payload: JsonObject,
) -> VideoFrameBoxJsonObject:
    if not isinstance(payload, Mapping):
        return {}
    return _normalize_mapping(cast(Mapping[object, JsonValue], payload))


def validate_video_frame_box_annotation_request(
    payload: JsonObject | list[JsonObject],
) -> VideoFrameBoxAnnotationRequestPayload:
    if isinstance(payload, list):
        return VideoFrameBoxAnnotationRequestPayload.model_validate(
            {"annotations": payload}
        )
    return VideoFrameBoxAnnotationRequestPayload.model_validate(payload)


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
