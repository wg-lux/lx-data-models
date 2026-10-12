"""Portable mask definitions; coordinates describe the image region to retain."""
from pydantic import BaseModel, ConfigDict, Field

from .video_processing import VideoMaskConfig


class VideoMaskProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{0,79}$")
    label: str = Field(min_length=1, max_length=160)
    device_name: str = Field(min_length=1, max_length=160)
    mask: VideoMaskConfig
