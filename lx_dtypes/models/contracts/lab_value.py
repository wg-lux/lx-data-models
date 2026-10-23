from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator


class LabValueNormalRangeBandPayload(BaseModel):
    model_config = ConfigDict(
        extra="forbid", frozen=True, strict=True, allow_inf_nan=False
    )

    min: float | None = None
    max: float | None = None

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError("normal range min must not exceed max")
        return self


class LabValueNormalRangeData(LabValueNormalRangeBandPayload):
    male: LabValueNormalRangeBandPayload | None = None
    female: LabValueNormalRangeBandPayload | None = None
    other: LabValueNormalRangeBandPayload | None = None


class LabValueNormalRangePayload(LabValueNormalRangeData):
    def to_data(self) -> LabValueNormalRangeData:
        return LabValueNormalRangeData.model_validate(self.model_dump())


__all__ = [
    "LabValueNormalRangeBandPayload",
    "LabValueNormalRangeData",
    "LabValueNormalRangePayload",
]
