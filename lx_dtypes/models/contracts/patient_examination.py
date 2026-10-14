from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PatientExaminationPatientDataPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    id: int = Field(ge=1)
    patient_hash: str = Field(min_length=1)
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)


__all__ = ["PatientExaminationPatientDataPayload"]
