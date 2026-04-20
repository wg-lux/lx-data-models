from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


class RequirementEvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_examination_id: int
    requirement_set_ids: list[int] | None = None

    @field_validator("patient_examination_id", mode="before")
    @classmethod
    def coerce_patient_examination_id(cls, value: Any) -> int:
        normalized = int(value)
        if normalized <= 0:
            raise ValueError("patient_examination_id must be a positive integer")
        return normalized

    @field_validator("requirement_set_ids", mode="before")
    @classmethod
    def coerce_requirement_set_ids(cls, value: Any) -> list[int] | None:
        if value in (None, ""):
            return None
        if not isinstance(value, list):
            raise ValueError("requirement_set_ids must be a list of positive integers")

        parsed: list[int] = []
        for item in value:
            normalized = int(item)
            if normalized <= 0:
                raise ValueError(
                    "requirement_set_ids must be a list of positive integers"
                )
            parsed.append(normalized)
        return parsed


class RequirementEvaluationMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_examination_id: int | None
    sets_evaluated: int
    requirements_evaluated: int
    status: str


class RequirementEvaluationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement_set_id: int
    requirement_set_name: str
    requirement_name: str
    met: bool
    details: str
    error: str | None
    status: str


class RequirementEvaluationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool
    errors: list[str]
    meta: RequirementEvaluationMeta
    results: list[RequirementEvaluationResult]


__all__ = [
    "RequirementEvaluationMeta",
    "RequirementEvaluationRequest",
    "RequirementEvaluationResponse",
    "RequirementEvaluationResult",
]
