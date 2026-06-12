from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from .endoscopy_processor import RoiBoxCore


class VideoEncoderConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    preset_param: str
    preset_value: str
    quality_param: str
    quality_value: str
    type: str
    fallback_preset: str

    @field_validator(
        "name",
        "preset_param",
        "preset_value",
        "quality_param",
        "quality_value",
        "type",
        "fallback_preset",
        mode="before",
    )
    @classmethod
    def normalize_non_empty_text(cls, value: object) -> str:
        normalized = str(value).strip()
        if not normalized:
            raise ValueError("value must not be empty")
        return normalized


class VideoMaskConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: int
    y: int
    width: int
    height: int
    image_width: int = 1920
    image_height: int = 1080

    @field_validator("x", "y", "width", "height", "image_width", "image_height")
    @classmethod
    def validate_int(cls, value: object) -> int:
        normalized = int(str(value))
        if normalized < 0:
            raise ValueError("value must be >= 0")
        return normalized

    @model_validator(mode="after")
    def validate_dimensions(self) -> "VideoMaskConfig":
        if self.width <= 0:
            raise ValueError("width must be > 0")
        if self.height <= 0:
            raise ValueError("height must be > 0")
        if self.image_width <= 0:
            raise ValueError("image_width must be > 0")
        if self.image_height <= 0:
            raise ValueError("image_height must be > 0")
        if self.x + self.width > self.image_width:
            raise ValueError("mask width exceeds image width")
        if self.y + self.height > self.image_height:
            raise ValueError("mask height exceeds image height")
        return self


class VideoMaskRegionCore(RoiBoxCore):
    model_config = ConfigDict(extra="forbid", strict=True)

    image_width: int
    image_height: int
    configured_x: int
    configured_y: int
    configured_width: int
    configured_height: int

    @field_validator("image_width", "image_height")
    @classmethod
    def validate_image_dimension(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("image dimensions must be > 0")
        return value

    @field_validator("configured_x", "configured_y")
    @classmethod
    def validate_config_origin(cls, value: int) -> int:
        if value < 0:
            raise ValueError("configured x and y must be >= 0")
        return value

    @field_validator("configured_width", "configured_height")
    @classmethod
    def validate_config_size(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("configured width and height must be > 0")
        return value


__all__ = ["VideoEncoderConfig", "VideoMaskConfig", "VideoMaskRegionCore"]
