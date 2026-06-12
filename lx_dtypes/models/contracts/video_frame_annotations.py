from __future__ import annotations

from collections.abc import Mapping
from typing import NotRequired, TypedDict, cast

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    field_validator,
    model_validator,
)

from .json_types import JsonObject


class FrameAnnotationBulkItemData(TypedDict):
    frame_id: int
    label_id: int
    value: bool
    float_value: NotRequired[float | None]
    information_source_name: str
    annotator: NotRequired[str | None]
    external_annotation_id: NotRequired[str | None]
    model_meta_id: NotRequired[int | None]


class FrameAnnotationBulkEnvelopeData(TypedDict, total=False):
    video_id: int | None
    ai_dataset_id: int | None
    annotations: list[JsonObject]


class FrameBoxAnnotationBulkItemData(FrameAnnotationBulkItemData, total=False):
    id: int | None
    x: float
    y: float
    width: float
    height: float
    image_width: int
    image_height: int


class FrameBoxAnnotationBulkEnvelopeData(TypedDict, total=False):
    frame_id: int | None
    video_id: int | None
    replace: bool
    annotator: str | None
    information_source_name: str | None
    information_source: str | None
    annotations: list[JsonObject]


class FrameAnnotationBulkItemPayload(BaseModel):
    model_config = ConfigDict(extra="allow", str_strip_whitespace=True)

    frame_id: int = Field(ge=1)
    label_id: int | None = Field(default=None, ge=1)
    choice_name: str | None = None
    value: bool = True
    float_value: float | None = None
    information_source_name: str = Field(min_length=1)
    annotator: str | None = None
    external_annotation_id: str | None = None
    model_meta_id: int | None = Field(default=None, ge=1)

    @field_validator(
        "choice_name", "annotator", "external_annotation_id", mode="before"
    )
    @classmethod
    def _blank_to_none(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip() or None
        return value

    @model_validator(mode="after")
    def validate_label_reference(self) -> FrameAnnotationBulkItemPayload:
        if self.label_id is None and not self.choice_name:
            raise ValueError("Either label_id or choice_name is required")
        return self


class FrameAnnotationBulkEnvelopePayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    video_id: int | None = Field(default=None, ge=1)
    ai_dataset_id: int | None = Field(default=None, ge=1)
    annotations: list[FrameAnnotationBulkItemPayload]


class FrameAnnotationSkipPayload(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    frame_id: int = Field(ge=1)
    video_id: int | None = Field(default=None, ge=1)
    annotator: str | None = None
    reason: str = ""
    information_source_name: str | None = None
    information_source: str | None = None
    exclude_annotated: bool = True

    @field_validator(
        "annotator", "information_source_name", "information_source", mode="before"
    )
    @classmethod
    def _blank_to_none(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip() or None
        return value


class FrameBoxAnnotationBulkItemPayload(FrameAnnotationBulkItemPayload):
    id: int | None = Field(default=None, ge=1)
    x: float = Field(ge=0)
    y: float = Field(ge=0)
    width: float = Field(gt=0)
    height: float = Field(gt=0)
    image_width: int = Field(gt=0)
    image_height: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_box_bounds(self) -> FrameBoxAnnotationBulkItemPayload:
        if self.x + self.width > self.image_width:
            raise ValueError("x + width must not exceed image_width")
        if self.y + self.height > self.image_height:
            raise ValueError("y + height must not exceed image_height")
        return self


class FrameBoxAnnotationBulkEnvelopePayload(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    frame_id: int | None = Field(default=None, ge=1)
    video_id: int | None = Field(default=None, ge=1)
    replace: bool = False
    annotator: str | None = None
    information_source_name: str | None = None
    information_source: str | None = None
    annotations: list[FrameBoxAnnotationBulkItemPayload]

    @field_validator(
        "annotator", "information_source_name", "information_source", mode="before"
    )
    @classmethod
    def _blank_to_none(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip() or None
        return value


class FrameAnnotationPayloadMapping(RootModel[JsonObject]):
    model_config = ConfigDict(frozen=True)

    @field_validator("root", mode="before")
    @classmethod
    def normalize_mapping(cls, value: object) -> object:
        if not isinstance(value, Mapping):
            raise ValueError("payload must be a JSON object")
        mapping = cast(Mapping[object, object], value)
        return {str(key): item for key, item in mapping.items()}

    def to_json_object(self) -> JsonObject:
        return cast(JsonObject, self.model_dump(mode="json"))


def dump_frame_annotation_bulk_item(
    payload: FrameAnnotationBulkItemPayload,
) -> FrameAnnotationBulkItemData:
    return cast(
        FrameAnnotationBulkItemData,
        payload.model_dump(mode="python", exclude_none=True),
    )


def dump_frame_box_annotation_bulk_item(
    payload: FrameBoxAnnotationBulkItemPayload,
) -> FrameBoxAnnotationBulkItemData:
    return cast(
        FrameBoxAnnotationBulkItemData,
        payload.model_dump(mode="python", exclude_none=True),
    )


__all__ = [
    "FrameAnnotationBulkEnvelopeData",
    "FrameAnnotationBulkEnvelopePayload",
    "FrameAnnotationBulkItemData",
    "FrameAnnotationBulkItemPayload",
    "FrameAnnotationPayloadMapping",
    "FrameAnnotationSkipPayload",
    "FrameBoxAnnotationBulkEnvelopeData",
    "FrameBoxAnnotationBulkEnvelopePayload",
    "FrameBoxAnnotationBulkItemData",
    "FrameBoxAnnotationBulkItemPayload",
    "dump_frame_annotation_bulk_item",
    "dump_frame_box_annotation_bulk_item",
]
