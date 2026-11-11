from __future__ import annotations

from pydantic import field_validator

from lx_dtypes.models.model import StrictContractModel


class VideoFrameDimensions(StrictContractModel):
    width: int
    height: int

    @field_validator("width", "height")
    @classmethod
    def validate_positive_dimension(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("frame dimensions must be > 0")
        return value


__all__ = ["VideoFrameDimensions"]
