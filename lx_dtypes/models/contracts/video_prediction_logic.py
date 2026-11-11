from __future__ import annotations

from pydantic import ConfigDict, Field

from lx_dtypes.models.model import DtypesModel

from .json_types import JsonValue


class PredictionSegmentCreatePayload(DtypesModel):
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    start_frame_number: int = Field(ge=0)
    end_frame_number: int = Field(ge=0)
    source: JsonValue
    label: JsonValue
    prediction_meta: JsonValue
    video_file: JsonValue


__all__ = ["PredictionSegmentCreatePayload"]
