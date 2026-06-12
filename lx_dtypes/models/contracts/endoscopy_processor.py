from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class RoiBoxCore(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    x: int
    y: int
    width: int
    height: int


class EndoscopeImageRoiCore(RoiBoxCore):
    image_width: int
    image_height: int


class EndoscopyProcessorCore(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    name: str


__all__ = [
    "RoiBoxCore",
    "EndoscopeImageRoiCore",
    "EndoscopyProcessorCore",
]
