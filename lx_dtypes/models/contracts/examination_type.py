from __future__ import annotations

from lx_dtypes.models.model import FrozenContractModel


class ExaminationTypeCore(FrozenContractModel):
    name: str


__all__ = ["ExaminationTypeCore"]
