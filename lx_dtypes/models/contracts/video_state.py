from __future__ import annotations

from collections.abc import Mapping
from pydantic import BaseModel, ConfigDict, Field


class VideoFrameStateContract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, from_attributes=True)

    frame_count: int | None = Field(default=None, ge=0)


def parse_video_frame_state_payload(
    payload: Mapping[str, int | float | str | bool | None] | None,
) -> VideoFrameStateContract:
    return VideoFrameStateContract.model_validate(payload or {})


__all__ = ["VideoFrameStateContract", "parse_video_frame_state_payload"]
