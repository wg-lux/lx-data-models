from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator


class NginxAccelResponseHeadersPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    content_type: str
    x_accel_redirect: str
    x_accel_buffering: str
    accept_ranges: str | None = None
    content_disposition: str | None = None

    @field_validator("content_type", "x_accel_redirect", "x_accel_buffering")
    @classmethod
    def normalize_required_header(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("header value must not be empty")
        return normalized


__all__ = ["NginxAccelResponseHeadersPayload"]
