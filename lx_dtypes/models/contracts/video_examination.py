from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime
from typing import NotRequired, TypedDict, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator


class VideoExaminationCreateData(TypedDict):
    video_id: int
    examination_id: int
    date_start: NotRequired[date | None]
    date_end: NotRequired[date | None]


class VideoExaminationUpdateData(TypedDict, total=False):
    examination_id: int
    date_start: date | None
    date_end: date | None


class VideoExaminationFindingData(TypedDict):
    id: int
    finding_id: int | None
    finding_name: str | None
    created_at: datetime | None


class VideoExaminationListQueryData(TypedDict, total=False):
    video_id: int
    patient_id: int
    examination_id: int


class VideoExaminationCreatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    video_id: int = Field(ge=1)
    examination_id: int = Field(ge=1)
    date_start: date | None = None
    date_end: date | None = None


class VideoExaminationUpdatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    examination_id: int | None = Field(default=None, ge=1)
    date_start: date | None = None
    date_end: date | None = None


class VideoExaminationFindingPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int = Field(ge=1)
    finding_id: int | None = Field(default=None, ge=1)
    finding_name: str | None = None
    created_at: datetime | None = None


class VideoExaminationListQueryPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    video_id: int | None = Field(default=None, ge=1)
    patient_id: int | None = Field(default=None, ge=1)
    examination_id: int | None = Field(default=None, ge=1)

    @field_validator("video_id", "patient_id", "examination_id", mode="before")
    @classmethod
    def normalize_optional_id(cls, value: object) -> object:
        if value in (None, ""):
            return None
        return value


class VideoExaminationPathPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    video_id: int = Field(ge=1)


def dump_video_examination_create_payload(
    payload: VideoExaminationCreatePayload,
) -> VideoExaminationCreateData:
    return cast(
        VideoExaminationCreateData,
        payload.model_dump(exclude_unset=True),
    )


def dump_video_examination_update_payload(
    payload: VideoExaminationUpdatePayload,
) -> VideoExaminationUpdateData:
    return cast(
        VideoExaminationUpdateData,
        payload.model_dump(exclude_unset=True),
    )


def dump_video_examination_finding_payload(
    payload: VideoExaminationFindingPayload,
) -> VideoExaminationFindingData:
    return cast(VideoExaminationFindingData, payload.model_dump())


def dump_video_examination_list_query_payload(
    payload: VideoExaminationListQueryPayload,
) -> VideoExaminationListQueryData:
    return cast(
        VideoExaminationListQueryData,
        payload.model_dump(exclude_none=True),
    )


def validate_video_examination_list_query(
    payload: Mapping[str, object],
) -> VideoExaminationListQueryPayload:
    return VideoExaminationListQueryPayload.model_validate(dict(payload))


def validate_video_examination_path_payload(
    payload: Mapping[str, object],
) -> VideoExaminationPathPayload:
    return VideoExaminationPathPayload.model_validate(dict(payload))


__all__ = [
    "VideoExaminationCreateData",
    "VideoExaminationCreatePayload",
    "VideoExaminationFindingData",
    "VideoExaminationFindingPayload",
    "VideoExaminationListQueryData",
    "VideoExaminationListQueryPayload",
    "VideoExaminationPathPayload",
    "VideoExaminationUpdateData",
    "VideoExaminationUpdatePayload",
    "dump_video_examination_create_payload",
    "dump_video_examination_finding_payload",
    "dump_video_examination_list_query_payload",
    "dump_video_examination_update_payload",
    "validate_video_examination_list_query",
    "validate_video_examination_path_payload",
]
