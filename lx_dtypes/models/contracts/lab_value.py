from __future__ import annotations

from typing import Self

from pydantic import ConfigDict, model_validator

from lx_dtypes.models.model import FrozenContractModel


class LabValueNormalRangeBandPayload(FrozenContractModel):
    model_config = ConfigDict(allow_inf_nan=False)

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
