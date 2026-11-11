from __future__ import annotations

from lx_dtypes.models.model import FrozenContractModel


class ExaminationTimeCore(FrozenContractModel):
    name: str


class ExaminationTimeTypeCore(FrozenContractModel):
    name: str


__all__ = ["ExaminationTimeCore", "ExaminationTimeTypeCore"]
