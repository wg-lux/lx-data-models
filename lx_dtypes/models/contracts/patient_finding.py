from __future__ import annotations

from uuid import UUID

from pydantic import Field

from lx_dtypes.models.model import FrozenContractModel, StrictContractModel


class PatientFindingIdentityPayload(StrictContractModel):
    """Stable lesion identity; omitted identifiers retain legacy singleton lookup."""

    patient_finding_id: int | None = Field(default=None, ge=1)
    instance_id: UUID | None = Field(default=None, strict=False)


class PatientFindingCore(FrozenContractModel):
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
