from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PatientFindingIdentityPayload(BaseModel):
    """Stable lesion identity; omitted identifiers retain legacy singleton lookup."""

    model_config = ConfigDict(extra="forbid", strict=True)

    patient_finding_id: int | None = Field(default=None, ge=1)
    instance_id: UUID | None = Field(default=None, strict=False)


class PatientFindingCore(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    patient_examination_id: int
    finding_name: str
    instance_id: UUID | None = None
    is_active: bool = True
    created_by_username: str = ""
    updated_by_username: str = ""
    deactivated_by_username: str = ""
    sub_related_classifications: list[str] = Field(default_factory=list)
    sub_related_interventions: list[str] = Field(default_factory=list)


__all__ = ["PatientFindingCore", "PatientFindingIdentityPayload"]
