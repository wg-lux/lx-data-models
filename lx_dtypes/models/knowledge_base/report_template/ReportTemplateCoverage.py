from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ReportTemplateCoverageConcept(BaseModel):
    """Authored, stable metadata used by the server-side coverage builder."""

    model_config = ConfigDict(extra="forbid", strict=True)

    concept_id: str = Field(pattern=r"^[a-z][a-z0-9_.:-]*$")
    label: str = Field(min_length=1)
    applicability_status: Literal["required", "conditional", "not_applicable"]
    applicability_rule: str | None = None
    applicability_reason: str | None = None
    validator_names: List[str] = Field(min_length=1)
    evidence_path: List[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_applicability(self) -> "ReportTemplateCoverageConcept":
        if self.applicability_status == "conditional" and not self.applicability_rule:
            raise ValueError("conditional coverage requires applicability_rule")
        if self.applicability_status == "not_applicable" and not self.applicability_reason:
            raise ValueError("not_applicable coverage requires applicability_reason")
        return self
