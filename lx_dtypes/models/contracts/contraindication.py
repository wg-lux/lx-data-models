from __future__ import annotations

from lx_dtypes.models.model import FrozenContractModel


class ContraindicationCore(FrozenContractModel):
    name: str
    description: str | None = None


__all__ = ["ContraindicationCore"]
