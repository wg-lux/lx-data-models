from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator


class VideoStreamInfoPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    codec_type: str
    width: int
    height: int
    avg_frame_rate: str | None = None
    r_frame_rate: str | None = None

    @field_validator("codec_type")
    @classmethod
    def validate_codec_type(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("codec_type must not be empty")
        return normalized

    @field_validator("width", "height")
    @classmethod
    def validate_dimension(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("video dimensions must be > 0")
        return value


class FfprobeStreamInfoPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    streams: list[VideoStreamInfoPayload]


__all__ = ["FfprobeStreamInfoPayload", "VideoStreamInfoPayload"]
