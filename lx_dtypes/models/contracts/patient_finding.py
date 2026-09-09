from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PatientFindingCore(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    patient_examination_id: int
    finding_name: str
    is_active: bool = True
    created_by_username: str = ""
    updated_by_username: str = ""
    deactivated_by_username: str = ""
    sub_related_classifications: list[str] = Field(default_factory=list)
    sub_related_interventions: list[str] = Field(default_factory=list)


__all__ = ["PatientFindingCore"]
