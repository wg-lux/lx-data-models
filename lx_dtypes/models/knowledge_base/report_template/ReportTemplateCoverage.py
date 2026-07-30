from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ReportTemplateCoverageFindingSelector(BaseModel):
    """Select every matching finding instance in examination order."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    finding_name: str = Field(min_length=1)
    classification_name: str | None = Field(default=None, min_length=1)
    classification_choice: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def validate_classification_choice(self) -> "ReportTemplateCoverageFindingSelector":
        if self.classification_choice and not self.classification_name:
            raise ValueError(
                "classification_choice requires classification_name in a finding selector"
            )
        return self


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
    concept_value_path: List[str] | None = None
    finding_selector: ReportTemplateCoverageFindingSelector | None = None
    allowed_values: List[str | int | float | bool] | None = None

    @model_validator(mode="after")
    def validate_applicability(self) -> "ReportTemplateCoverageConcept":
        if self.applicability_status == "conditional" and not self.applicability_rule:
            raise ValueError("conditional coverage requires applicability_rule")
        if (
            self.applicability_status == "not_applicable"
            and not self.applicability_reason
        ):
            raise ValueError("not_applicable coverage requires applicability_reason")
        if self.applicability_status != "not_applicable":
            if not self.concept_value_path and not self.finding_selector:
                raise ValueError(
                    "applicable coverage requires concept_value_path or finding_selector"
                )
            if not self.allowed_values:
                raise ValueError(
                    "applicable coverage requires non-empty allowed_values for semantic value checking"
                )
        return self
