from __future__ import annotations

from typing import Literal

from pydantic import Field

from lx_dtypes.models.model import FrozenContractModel


class PatientDeletionRelatedObjectsPayload(FrozenContractModel):
    examinations: int = Field(ge=0)
    findings: int = Field(ge=0)
    videos: int = Field(ge=0)
    reports: int = Field(ge=0)


class PatientDeletionSafetyPayload(FrozenContractModel):
    can_delete: bool
    is_real_person: bool
    related_objects: PatientDeletionRelatedObjectsPayload
    warnings: list[str]


class PatientPseudonymPayload(FrozenContractModel):
    patient_id: int | str
    source: Literal["server"]
    persisted: bool
    message: str = Field(min_length=1)


__all__ = [
    "PatientDeletionRelatedObjectsPayload",
    "PatientDeletionSafetyPayload",
    "PatientPseudonymPayload",
]
