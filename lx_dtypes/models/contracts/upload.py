from __future__ import annotations

from collections.abc import Mapping
from typing import TypedDict

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

_UPLOAD_API_REQUEST_FIELD_NAMES = frozenset(
    {"center_key", "center_name", "source_system", "idempotency_key"}
)
_UPLOAD_API_TRANSPORT_FIELD_NAMES = frozenset({"file"})


class UploadApiRequestData(TypedDict, total=False):
    center_key: str
    center_name: str
    source_system: str
    idempotency_key: str


class UploadApiRequestPayload(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        strict=True,
    )

    center_key: str = Field(default="", max_length=255)
    center_name: str = Field(default="", max_length=255)
    source_system: str = Field(default="api", min_length=1, max_length=255)
    idempotency_key: str = Field(default="", max_length=255)

    @field_validator("source_system", mode="after")
    @classmethod
    def normalize_source_system(cls, value: str) -> str:
        return value or "api"


def upload_api_request_data_from_mapping(
    payload: Mapping[str, object],
) -> UploadApiRequestData:
    unknown_field_names = (
        set(payload)
        - _UPLOAD_API_REQUEST_FIELD_NAMES
        - _UPLOAD_API_TRANSPORT_FIELD_NAMES
    )
    if unknown_field_names:
        formatted_names = ", ".join(sorted(unknown_field_names))
        raise ValueError(f"Unknown upload request field(s): {formatted_names}")

    def optional_text(field_name: str) -> str | None:
        if field_name not in payload:
            return None
        raw_value = payload[field_name]
        if not isinstance(raw_value, str):
            raise ValueError(  # noqa: TRY004 - public validation contract
                f"{field_name} must be a string"
            )
        return raw_value.strip() or None

    data: UploadApiRequestData = {}
    center_key = optional_text("center_key")
    center_name = optional_text("center_name")
    source_system = optional_text("source_system")
    idempotency_key = optional_text("idempotency_key")
    if center_key is not None:
        data["center_key"] = center_key
    if center_name is not None:
        data["center_name"] = center_name
    if source_system is not None:
        data["source_system"] = source_system
    if idempotency_key is not None:
        data["idempotency_key"] = idempotency_key
    return data


def validate_upload_api_request_payload(
    value: Mapping[str, object],
) -> UploadApiRequestPayload:
    try:
        return UploadApiRequestPayload.model_validate(
            upload_api_request_data_from_mapping(value)
        )
    except (
        ValidationError,
        ValueError,
    ) as exc:  # pragma: no cover - thin validation wrapper
        raise ValueError(str(exc)) from exc


__all__ = [
    "UploadApiRequestData",
    "UploadApiRequestPayload",
    "upload_api_request_data_from_mapping",
    "validate_upload_api_request_payload",
]
