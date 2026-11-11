from __future__ import annotations

from lx_dtypes.models.model import FrozenContractModel


class FindingInterventionCore(FrozenContractModel):
    name: str
    description: str | None = None


class FindingInterventionTypeCore(FrozenContractModel):
    name: str
    description: str | None = None


__all__ = ["FindingInterventionCore", "FindingInterventionTypeCore"]
