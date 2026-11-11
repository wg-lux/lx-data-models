from __future__ import annotations

from pydantic import Field

from lx_dtypes.models.model import FrozenContractModel


class NginxAccelResponseHeadersPayload(FrozenContractModel):
    content_type: str = Field(min_length=1)
    x_accel_redirect: str = Field(min_length=1)
    x_accel_buffering: str = Field(min_length=1)
    accept_ranges: str | None = None
    content_disposition: str | None = None


__all__ = ["NginxAccelResponseHeadersPayload"]
