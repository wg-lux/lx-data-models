from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class NginxAccelResponseHeadersPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    content_type: str = Field(min_length=1)
    x_accel_redirect: str = Field(min_length=1)
    x_accel_buffering: str = Field(min_length=1)
    accept_ranges: str | None = None
    content_disposition: str | None = None


__all__ = ["NginxAccelResponseHeadersPayload"]
