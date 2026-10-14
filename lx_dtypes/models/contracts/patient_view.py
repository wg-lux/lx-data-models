from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PatientDeletionRelatedObjectsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    examinations: int = Field(ge=0)
    findings: int = Field(ge=0)
    videos: int = Field(ge=0)
    reports: int = Field(ge=0)


class PatientDeletionSafetyPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    can_delete: bool
    is_real_person: bool
    related_objects: PatientDeletionRelatedObjectsPayload
    warnings: list[str]


class PatientPseudonymPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    patient_id: int | str
    patient_hash: str = Field(min_length=1)
    source: Literal["server"]
    persisted: bool
    message: str = Field(min_length=1)


__all__ = [
    "PatientDeletionRelatedObjectsPayload",
    "PatientDeletionSafetyPayload",
    "PatientPseudonymPayload",
]
