from __future__ import annotations

from collections.abc import Mapping
from typing import cast

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    ValidationError,
    field_validator,
    model_validator,
)

from .json_types import JsonObject, JsonValue

type VideoSegmentsPayloadDict = dict[str, list[tuple[int, int]]]


class VideoSegmentsPayload(RootModel[VideoSegmentsPayloadDict]):
    model_config = ConfigDict(strict=True)

    @property
    def as_dict(self) -> VideoSegmentsPayloadDict:
        return self.root


class SegmentAnnotationMetadataInput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    segment_id: int | None = None


class SegmentAnnotationInput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    annotation_type: str = Field(alias="type")
    video_id: int = Field(gt=0)
    start_time: float = Field(ge=0)
    end_time: float = Field(ge=0)
    text: str = ""
    tags: list[str] = Field(default_factory=list)
    metadata: SegmentAnnotationMetadataInput = Field(
        default_factory=SegmentAnnotationMetadataInput
    )

    @model_validator(mode="after")
    def validate_segment_annotation(self) -> SegmentAnnotationInput:
        if self.annotation_type != "segment":
            raise ValueError("annotation type must be 'segment'")
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be greater than start_time")
        return self

    def to_frame_range(self, fps: float) -> tuple[int, int]:
        return (
            round(self.start_time * fps),
            round(self.end_time * fps),
        )


def validate_video_segments_payload(
    value: VideoSegmentsPayloadDict | Mapping[str, list[tuple[int, int]]],
) -> VideoSegmentsPayload:
    return VideoSegmentsPayload.model_validate(value)


def parse_segment_annotation_input(
    annotation: SegmentAnnotationInput | Mapping[str, JsonValue],
) -> SegmentAnnotationInput | None:
    if isinstance(annotation, SegmentAnnotationInput):
        return annotation

    try:
        return SegmentAnnotationInput.model_validate(annotation)
    except ValidationError:
        return None


def _blank_to_none(value: str | float | bool | None) -> str | None:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    if value is None:
        return None
    return str(value).strip() or None


def _payload_dict(payload: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    return dict(payload)


def _empty_segment_id_list() -> list[int]:
    return []


def _empty_bulk_validation_item_list() -> list[SegmentBulkValidationItem]:
    return []


class SegmentCrudPayload(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    ai_dataset_id: int | None = Field(default=None, ge=1)
    video_id: int | None = Field(default=None, ge=1)
    video_file: int | None = Field(default=None, ge=1)
    label_id: int | None = Field(default=None, ge=1)
    label: int | None = Field(default=None, ge=1)
    label_name: str | None = None
    start_frame_number: int | None = Field(default=None, ge=0)
    end_frame_number: int | None = Field(default=None, ge=0)
    start_time: float | None = Field(default=None, ge=0)
    end_time: float | None = Field(default=None, ge=0)
    export_segment: bool | None = None

    @field_validator("label_name", mode="before")
    @classmethod
    def _normalize_label_name(cls, value: str | float | bool | None) -> str | None:
        return _blank_to_none(value)

    @model_validator(mode="after")
    def _validate_segment_bounds(self) -> SegmentCrudPayload:
        if (
            self.start_frame_number is not None
            and self.end_frame_number is not None
            and self.end_frame_number <= self.start_frame_number
        ):
            raise ValueError("end_frame_number must be greater than start_frame_number")

        if self.start_time is not None and self.end_time is not None:
            SegmentAnnotationInput.model_validate(
                {
                    "type": "segment",
                    "video_id": self.video_id or self.video_file or 1,
                    "start_time": self.start_time,
                    "end_time": self.end_time,
                    "metadata": {},
                }
            )
        return self

    def serializer_payload(self, *, video_id: int | None = None) -> JsonObject:
        payload = cast(
            JsonObject,
            self.model_dump(
                mode="python",
                exclude={"ai_dataset_id"},
                exclude_unset=True,
            ),
        )
        if payload.get("video_file") is not None and payload.get("video_id") is None:
            payload["video_id"] = payload["video_file"]
        payload.pop("video_file", None)
        if payload.get("label") is not None and payload.get("label_id") is None:
            payload["label_id"] = payload["label"]
        payload.pop("label", None)
        if video_id is not None:
            payload["video_id"] = video_id
        return payload


class SegmentListQuery(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    video_id: int | None = Field(default=None, ge=1)
    label_id: int | None = Field(default=None, ge=1)
    label: str | None = None
    source_kind: str | None = None
    include_annotation_payload: bool = False

    @field_validator("label", "source_kind", mode="before")
    @classmethod
    def _normalize_optional_text(cls, value: str | float | bool | None) -> str | None:
        return _blank_to_none(value)


class SegmentBlackenOutsidePayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    only_validated: bool = False


class SegmentValidationPayload(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    is_validated: bool = True
    information_source_name: str = "manual_annotation"
    annotator: str | None = None
    start_time: float | None = Field(default=None, ge=0)
    end_time: float | None = Field(default=None, ge=0)

    @field_validator("information_source_name", mode="before")
    @classmethod
    def _default_information_source(cls, value: str | float | bool | None) -> str:
        normalized = _blank_to_none(value)
        return str(normalized or "manual_annotation")

    @field_validator("annotator", mode="before")
    @classmethod
    def _normalize_annotator(cls, value: str | float | bool | None) -> str | None:
        return _blank_to_none(value)

    @model_validator(mode="after")
    def _validate_optional_timing_pair(self) -> SegmentValidationPayload:
        has_start = self.start_time is not None
        has_end = self.end_time is not None
        if has_start != has_end:
            raise ValueError("start_time and end_time must be provided together")
        if has_start and has_end:
            SegmentAnnotationInput.model_validate(
                {
                    "type": "segment",
                    "video_id": 1,
                    "start_time": self.start_time,
                    "end_time": self.end_time,
                    "metadata": {},
                }
            )
        return self

    def to_annotation_input(self, *, video_id: int) -> SegmentAnnotationInput | None:
        if self.start_time is None or self.end_time is None:
            return None
        return SegmentAnnotationInput.model_validate(
            {
                "type": "segment",
                "video_id": video_id,
                "start_time": self.start_time,
                "end_time": self.end_time,
                "metadata": {},
            }
        )


class SegmentBulkValidationItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int = Field(gt=0)
    start_time: float | None = Field(default=None, ge=0)
    end_time: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _validate_optional_timing_pair(self) -> SegmentBulkValidationItem:
        has_start = self.start_time is not None
        has_end = self.end_time is not None
        if has_start != has_end:
            raise ValueError("start_time and end_time must be provided together")
        if has_start and has_end:
            SegmentAnnotationInput.model_validate(
                {
                    "type": "segment",
                    "video_id": 1,
                    "start_time": self.start_time,
                    "end_time": self.end_time,
                    "metadata": {},
                }
            )
        return self

    def to_annotation_input(self, *, video_id: int) -> SegmentAnnotationInput | None:
        if self.start_time is None or self.end_time is None:
            return None
        return SegmentAnnotationInput.model_validate(
            {
                "type": "segment",
                "video_id": video_id,
                "start_time": self.start_time,
                "end_time": self.end_time,
                "metadata": {},
            }
        )


class SegmentBulkValidationPayload(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    segment_ids: list[int] = Field(default_factory=_empty_segment_id_list)
    segments: list[SegmentBulkValidationItem] = Field(
        default_factory=_empty_bulk_validation_item_list
    )
    is_validated: bool = True
    notes: str = ""
    information_source_name: str = "manual_annotation"
    annotator: str | None = None

    @field_validator("segment_ids", mode="before")
    @classmethod
    def _normalize_segment_ids(
        cls, value: list[int] | tuple[int, ...] | int | str | None
    ) -> list[int] | None:
        if value is None:
            return []
        if isinstance(value, list):
            return [
                cast(int, item)
                for item in cast(list[object], value)
                if item is not None
            ]
        return [cast(int, value)]

    @field_validator("information_source_name", mode="before")
    @classmethod
    def _default_information_source(cls, value: str | float | bool | None) -> str:
        normalized = _blank_to_none(value)
        return str(normalized or "manual_annotation")

    @field_validator("annotator", mode="before")
    @classmethod
    def _normalize_annotator(cls, value: str | float | bool | None) -> str | None:
        return _blank_to_none(value)

    @field_validator("notes", mode="before")
    @classmethod
    def _default_notes(cls, value: str | float | bool | None) -> str:
        return str(value or "")

    @model_validator(mode="after")
    def _validate_segment_ids(self) -> SegmentBulkValidationPayload:
        if any(segment_id <= 0 for segment_id in self.segment_ids):
            raise ValueError("segment_ids must contain positive integers")
        return self

    @property
    def timing_by_segment_id(self) -> dict[int, SegmentBulkValidationItem]:
        return {item.id: item for item in self.segments}


class SegmentPredictionImportItem(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    label_name: str | None = None
    label: str | None = None
    start_time: float = Field(ge=0)
    end_time: float = Field(ge=0)
    export_segment: bool = False

    @field_validator("label_name", "label", mode="before")
    @classmethod
    def _normalize_label_text(cls, value: str | float | bool | None) -> str | None:
        return _blank_to_none(value)

    @model_validator(mode="after")
    def _validate_import_item(self) -> SegmentPredictionImportItem:
        if not (self.label_name or self.label):
            raise ValueError("label_name or label is required")
        SegmentAnnotationInput.model_validate(
            {
                "type": "segment",
                "video_id": 1,
                "start_time": self.start_time,
                "end_time": self.end_time,
                "metadata": {},
            }
        )
        return self

    def serializer_payload(self, *, video_id: int) -> JsonObject:
        return {
            "video_id": video_id,
            "label_name": self.label_name or self.label,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "export_segment": self.export_segment,
        }


class SegmentPredictionImportPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    segments: list[SegmentPredictionImportItem] = Field(min_length=1)
    replace_existing: bool = True


class SegmentAnnotationEnsurePayload(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    video_ids: list[int] | None = None
    segment_ids: list[int] | None = None
    information_source_name: str = "manual_annotation"

    @field_validator("video_ids", "segment_ids", mode="before")
    @classmethod
    def _normalize_optional_int_list(
        cls, value: list[int] | tuple[int, ...] | int | str | None
    ) -> list[int] | None:
        if value is None:
            return None
        if isinstance(value, list):
            return [
                cast(int, item)
                for item in cast(list[object], value)
                if item is not None
            ]
        return [cast(int, value)]

    @field_validator("information_source_name", mode="before")
    @classmethod
    def _default_information_source(cls, value: str | float | bool | None) -> str:
        normalized = _blank_to_none(value)
        return str(normalized or "manual_annotation")

    @model_validator(mode="after")
    def _validate_ids(self) -> SegmentAnnotationEnsurePayload:
        for field_name in ("video_ids", "segment_ids"):
            values = getattr(self, field_name)
            if values is not None and any(value <= 0 for value in values):
                raise ValueError(f"{field_name} must contain positive integers")
        return self


class SegmentValidationStatusPayload(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    label_name: str | None = None

    @field_validator("label_name", mode="before")
    @classmethod
    def _normalize_label_name(cls, value: str | float | bool | None) -> str | None:
        return _blank_to_none(value)


def validate_segment_crud_payload(
    payload: Mapping[str, JsonValue],
) -> SegmentCrudPayload:
    return SegmentCrudPayload.model_validate(_payload_dict(payload))


def validate_segment_list_query(payload: Mapping[str, JsonValue]) -> SegmentListQuery:
    return SegmentListQuery.model_validate(_payload_dict(payload))


def validate_segment_blacken_outside_payload(
    payload: Mapping[str, JsonValue],
) -> SegmentBlackenOutsidePayload:
    return SegmentBlackenOutsidePayload.model_validate(_payload_dict(payload))


def validate_segment_validation_payload(
    payload: Mapping[str, JsonValue],
) -> SegmentValidationPayload:
    return SegmentValidationPayload.model_validate(_payload_dict(payload))


def validate_segment_bulk_validation_payload(
    payload: Mapping[str, JsonValue],
) -> SegmentBulkValidationPayload:
    return SegmentBulkValidationPayload.model_validate(_payload_dict(payload))


def validate_segment_prediction_import_payload(
    payload: Mapping[str, JsonValue],
) -> SegmentPredictionImportPayload:
    return SegmentPredictionImportPayload.model_validate(_payload_dict(payload))


def validate_segment_annotation_ensure_payload(
    payload: Mapping[str, JsonValue],
    *,
    default_information_source_name: str,
) -> SegmentAnnotationEnsurePayload:
    data = _payload_dict(payload)
    data.setdefault("information_source_name", default_information_source_name)
    return SegmentAnnotationEnsurePayload.model_validate(data)


def validate_segment_validation_status_payload(
    payload: Mapping[str, JsonValue],
) -> SegmentValidationStatusPayload:
    return SegmentValidationStatusPayload.model_validate(_payload_dict(payload))


__all__ = [
    "SegmentAnnotationEnsurePayload",
    "SegmentAnnotationInput",
    "SegmentAnnotationMetadataInput",
    "SegmentBlackenOutsidePayload",
    "SegmentBulkValidationItem",
    "SegmentBulkValidationPayload",
    "SegmentCrudPayload",
    "SegmentListQuery",
    "SegmentPredictionImportItem",
    "SegmentPredictionImportPayload",
    "SegmentValidationPayload",
    "SegmentValidationStatusPayload",
    "VideoSegmentsPayload",
    "VideoSegmentsPayloadDict",
    "parse_segment_annotation_input",
    "validate_segment_annotation_ensure_payload",
    "validate_segment_blacken_outside_payload",
    "validate_segment_bulk_validation_payload",
    "validate_segment_crud_payload",
    "validate_segment_list_query",
    "validate_segment_prediction_import_payload",
    "validate_segment_validation_payload",
    "validate_segment_validation_status_payload",
    "validate_video_segments_payload",
]
