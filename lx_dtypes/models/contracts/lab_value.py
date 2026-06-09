from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class LabValueNormalRangePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    min: float | None = None
    max: float | None = None


class LabValueNormalRangeGenderData(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    min: float | None = None
    max: float | None = None


class LabValueNormalRangeData(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    min: float | None = None
    max: float | None = None
    male: LabValueNormalRangeGenderData | None = None
    female: LabValueNormalRangeGenderData | None = None


__all__ = [
    "LabValueNormalRangeData",
    "LabValueNormalRangeGenderData",
    "LabValueNormalRangePayload",
]
