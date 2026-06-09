from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


class UploadApiRequestPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file_name: str
    content_type: str | None = None
    size_bytes: int | None = None

    @field_validator("file_name", mode="before")
    @classmethod
    def normalize_file_name(cls, value: Any) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("file_name must not be empty")
        return normalized

    @field_validator("content_type", mode="before")
    @classmethod
    def normalize_content_type(cls, value: Any) -> str | None:
        if value in (None, ""):
            return None
        normalized = str(value).strip()
        return normalized or None

    @field_validator("size_bytes", mode="before")
    @classmethod
    def normalize_size_bytes(cls, value: Any) -> int | None:
        if value in (None, ""):
            return None
        normalized = int(value)
        if normalized < 0:
            raise ValueError("size_bytes must be >= 0")
        return normalized


def validate_upload_api_request_payload(value: Any) -> UploadApiRequestPayload:
    return UploadApiRequestPayload.model_validate(value)


__all__ = [
    "UploadApiRequestPayload",
    "validate_upload_api_request_payload",
]
