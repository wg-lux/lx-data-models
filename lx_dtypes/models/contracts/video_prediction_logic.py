from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PredictionSegmentCreatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    start_frame_number: int = Field(ge=0)
    end_frame_number: int = Field(ge=0)
    source: object
    label: object
    prediction_meta: object
    video_file: object


__all__ = ["PredictionSegmentCreatePayload"]
