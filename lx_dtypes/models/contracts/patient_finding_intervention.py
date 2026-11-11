from __future__ import annotations

from lx_dtypes.models.model import FrozenContractModel


class PatientFindingInterventionCore(FrozenContractModel):
    patient_finding_id: int
    intervention_name: str
    is_active: bool = True
    state: str | None = None


__all__ = ["PatientFindingInterventionCore"]
