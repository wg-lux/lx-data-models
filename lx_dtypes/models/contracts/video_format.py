from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator


class VideoFormatInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    video_codec: str = "unknown"
    pixel_format: str = "unknown"
    width: int = 0
    height: int = 0
    has_audio: bool = True
    container: str = "unknown"
    can_stream_copy: bool = False

    @field_validator("video_codec", "pixel_format", "container", mode="before")
    @classmethod
    def normalize_text(cls, value: str | float | bool | None) -> str:
        normalized = str(value).strip()
        return normalized or "unknown"

    @field_validator("width", "height", mode="before")
    @classmethod
    def normalize_size(cls, value: str | float | bool | None) -> int:
        normalized = int(str(value))
        if normalized < 0:
            raise ValueError("size values must be >= 0")
        return normalized


__all__ = ["VideoFormatInfo"]
