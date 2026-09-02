from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class LabValueNormalRangeBandPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    min: float | None = None
    max: float | None = None


class LabValueNormalRangeData(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    min: float | None = None
    max: float | None = None
    male: LabValueNormalRangeBandPayload | None = None
    female: LabValueNormalRangeBandPayload | None = None
    other: LabValueNormalRangeBandPayload | None = None


class LabValueNormalRangePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    min: float | None = None
    max: float | None = None
    male: LabValueNormalRangeBandPayload | None = None
    female: LabValueNormalRangeBandPayload | None = None
    other: LabValueNormalRangeBandPayload | None = None

    def to_data(self) -> LabValueNormalRangeData:
        return LabValueNormalRangeData.model_validate(self.model_dump())


__all__ = [
    "LabValueNormalRangeBandPayload",
    "LabValueNormalRangeData",
    "LabValueNormalRangePayload",
]
