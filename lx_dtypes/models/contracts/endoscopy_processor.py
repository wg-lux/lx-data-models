from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator


class RoiBoxCore(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    x: int
    y: int
    width: int
    height: int

    @field_validator("x", "y")
    @classmethod
    def validate_origin(cls, value: int) -> int:
        if value < 0:
            raise ValueError("x and y must be >= 0")
        return value

    @field_validator("width", "height")
    @classmethod
    def validate_size(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("width and height must be > 0")
        return value


class EndoscopeImageRoiCore(RoiBoxCore):
    image_width: int
    image_height: int

    @field_validator("image_width", "image_height")
    @classmethod
    def validate_image_dimension(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("image dimensions must be > 0")
        return value


__all__ = [
    "EndoscopeImageRoiCore",
    "RoiBoxCore",
]
