from __future__ import annotations

from typing import Any, TypeAlias

from pydantic import BaseModel, ConfigDict, Field

JsonObject: TypeAlias = dict[str, Any]


class FfmpegMetaPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    width: int | None = Field(default=None, ge=1)
    height: int | None = Field(default=None, ge=1)
    duration: float | None = Field(default=None, ge=0.0)
    frame_rate_num: int | None = Field(default=None, ge=0)
    frame_rate_den: int | None = Field(default=None, ge=0)
    codec_name: str | None = None
    pixel_format: str | None = None
    bit_rate: int | None = Field(default=None, ge=0)
    raw_probe_data: JsonObject | None = None


__all__ = ["FfmpegMetaPayload", "JsonObject"]
