from __future__ import annotations

from datetime import datetime
from typing import Literal, TypedDict

from pydantic import BaseModel, ConfigDict, Field, field_validator

AnonymizationMediaType = Literal["video", "pdf"]
AnonymizationStartResult = Literal["video", "pdf"]
AnonymizationValidationResult = Literal["video", "pdf"]


class AnonymizationStatusData(TypedDict):
    media_type: AnonymizationMediaType
    anonymization_status: str
    file_exists: bool
    integrity_status: str | None
    integrity_error: str | None
    uuid: str | None
    hash: str | None


class AnonymizationListItemData(TypedDict):
    id: int
    media_type: AnonymizationMediaType
    anonymization_status: str
    created_at: datetime | None
    updated_at: datetime | None


class AnonymizationStatusPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    media_type: AnonymizationMediaType
    anonymization_status: str
    file_exists: bool
    integrity_status: str | None = None
    integrity_error: str | None = None
    uuid: str | None = None
    hash: str | None = None

    @field_validator(
        "anonymization_status",
        "integrity_status",
        "integrity_error",
        "uuid",
        "hash",
        mode="before",
    )
    @classmethod
    def blank_to_none(cls, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, str):
            return value.strip() or None
        return str(value).strip() or None


class AnonymizationListItemPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    id: int = Field(ge=1)
    media_type: AnonymizationMediaType
    anonymization_status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


def dump_anonymization_status_payload(
    payload: AnonymizationStatusPayload,
) -> AnonymizationStatusData:
    return AnonymizationStatusData(
        media_type=payload.media_type,
        anonymization_status=payload.anonymization_status,
        file_exists=payload.file_exists,
        integrity_status=payload.integrity_status,
        integrity_error=payload.integrity_error,
        uuid=payload.uuid,
        hash=payload.hash,
    )


def dump_anonymization_list_item_payload(
    payload: AnonymizationListItemPayload,
) -> AnonymizationListItemData:
    return AnonymizationListItemData(
        id=payload.id,
        media_type=payload.media_type,
        anonymization_status=payload.anonymization_status,
        created_at=payload.created_at,
        updated_at=payload.updated_at,
    )


__all__ = [
    "AnonymizationListItemData",
    "AnonymizationListItemPayload",
    "AnonymizationMediaType",
    "AnonymizationStartResult",
    "AnonymizationStatusData",
    "AnonymizationStatusPayload",
    "AnonymizationValidationResult",
    "dump_anonymization_list_item_payload",
    "dump_anonymization_status_payload",
]
