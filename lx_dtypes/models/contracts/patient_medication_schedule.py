from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PatientMedicationScheduleCreateByIndicationTypePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    patient_id: int = Field(gt=0)
    indication_type: str = Field(min_length=1)


__all__ = ["PatientMedicationScheduleCreateByIndicationTypePayload"]
