from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class PatientFindingInterventionCore(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    patient_finding_id: int
    intervention_name: str
    is_active: bool = True
    state: str | None = None


__all__ = ["PatientFindingInterventionCore"]
