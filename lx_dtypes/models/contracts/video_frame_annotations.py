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

from .json_types import JsonObject, JsonValue


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
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

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
    def _blank_to_none(cls, value: str | float | bool | None) -> str | None:
        if isinstance(value, str):
            return value.strip() or None
        if value is None:
            return None
        return str(value).strip() or None

    @model_validator(mode="after")
    def validate_label_reference(self) -> FrameAnnotationBulkItemPayload:
        if self.label_id is None and not self.choice_name:
            raise ValueError("Either label_id or choice_name is required")
        return self


class FrameAnnotationBulkEnvelopePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    video_id: int | None = Field(default=None, ge=1)
    ai_dataset_id: int | None = Field(default=None, ge=1)
    annotations: list[FrameAnnotationBulkItemPayload]


class FrameAnnotationSkipPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

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
    def _blank_to_none(cls, value: str | float | bool | None) -> str | None:
        if isinstance(value, str):
            return value.strip() or None
        if value is None:
            return None
        return str(value).strip() or None


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
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    frame_id: int | None = Field(default=None, ge=1)
    video_id: int | None = Field(default=None, ge=1)
    replace: bool = False
    annotator: str | None = None
    information_source_name: str | None = None
    information_source: str | None = None
    annotations: list[FrameBoxAnnotationBulkItemPayload]

    @model_validator(mode="before")
    @classmethod
    def normalize_item_frame_ids(
        cls,
        value: Mapping[str, JsonValue] | None,
    ) -> Mapping[str, JsonValue] | None:
        if not isinstance(value, Mapping):
            return value

        mapping = cast(Mapping[object, JsonValue], value)
        outer_frame_id = mapping.get("frame_id")
        wrapper_source = mapping.get("information_source_name")
        if isinstance(wrapper_source, str):
            wrapper_source = wrapper_source.strip() or None
        if wrapper_source is None:
            wrapper_source = mapping.get("information_source")
            if isinstance(wrapper_source, str):
                wrapper_source = wrapper_source.strip() or None
        if wrapper_source is None:
            wrapper_source = "manual_annotation"
        wrapper_annotator = mapping.get("annotator")
        if isinstance(wrapper_annotator, str):
            wrapper_annotator = wrapper_annotator.strip() or None
        annotations = mapping.get("annotations")
        if not isinstance(annotations, list):
            return value

        normalized_envelope = {str(key): val for key, val in mapping.items()}

        normalized_annotations: list[JsonValue] = []
        for item in annotations:
            if not isinstance(item, Mapping):
                normalized_annotations.append(cast(JsonValue, item))
                continue
            item_mapping = {str(key): value for key, value in item.items()}
            if outer_frame_id is not None and "frame_id" not in item_mapping:
                item_mapping["frame_id"] = cast(JsonValue, outer_frame_id)
            if "information_source_name" not in item_mapping:
                item_mapping["information_source_name"] = cast(
                    JsonValue, wrapper_source
                )
            if wrapper_annotator is not None and "annotator" not in item_mapping:
                item_mapping["annotator"] = cast(JsonValue, wrapper_annotator)
            normalized_annotations.append(cast(JsonValue, item_mapping))

        normalized_envelope["annotations"] = cast(JsonValue, normalized_annotations)
        return normalized_envelope

    @model_validator(mode="after")
    def validate_item_frame_ids(self) -> FrameBoxAnnotationBulkEnvelopePayload:
        if self.frame_id is None:
            return self
        if any(item.frame_id != self.frame_id for item in self.annotations):
            raise ValueError("annotation frame_id must match the envelope frame_id")
        return self

    @field_validator(
        "annotator", "information_source_name", "information_source", mode="before"
    )
    @classmethod
    def _blank_to_none(cls, value: str | float | bool | None) -> str | None:
        if isinstance(value, str):
            return value.strip() or None
        return str(value)

    @property
    def resolved_information_source_name(self) -> str | None:
        return self.information_source_name or self.information_source


class FrameAnnotationPayloadMapping(RootModel[JsonObject]):
    model_config = ConfigDict(frozen=True)

    @field_validator("root", mode="before")
    @classmethod
    def normalize_mapping(cls, value: Mapping[str, JsonValue]) -> JsonObject:
        if not isinstance(value, Mapping):
            raise ValueError(  # noqa: TRY004 - Pydantic validator contract
                "payload must be a JSON object"
            )
        mapping = cast(Mapping[object, JsonValue], value)
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
