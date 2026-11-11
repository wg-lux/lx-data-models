"""Portable mask definitions; coordinates describe the image region to retain."""

from pydantic import ConfigDict, Field

from lx_dtypes.models.model import DtypesModel

from .video_processing import VideoMaskConfig


class VideoMaskProfile(DtypesModel):
    model_config = ConfigDict(frozen=True)

    name: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{0,79}$")
    label: str = Field(min_length=1, max_length=160)
    device_name: str = Field(min_length=1, max_length=160)
    mask: VideoMaskConfig
