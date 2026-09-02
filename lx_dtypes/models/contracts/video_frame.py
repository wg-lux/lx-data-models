from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator


class VideoFrameDimensions(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    width: int
    height: int

    @field_validator("width", "height")
    @classmethod
    def validate_positive_dimension(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("frame dimensions must be > 0")
        return value


__all__ = ["VideoFrameDimensions"]
