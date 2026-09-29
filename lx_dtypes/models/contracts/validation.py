"""Transport contracts for advisory validation; findings never authorize writes."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field

from .knowledge_base import KnowledgeBaseIdentity


class ValidationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    level: Literal["error", "warning"] = "error"
    source: Literal["contract", "terminology", "study"]
    path: tuple[str | int, ...] = ()
    validator_name: str | None = None


class ValidationReport(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    schema_version: Literal["1.0"] = "1.0"
    issues: tuple[ValidationIssue, ...] = ()
    knowledge_base_identity: KnowledgeBaseIdentity | None = None
    study_evaluated: bool = False

    @computed_field
    @property
    def ok(self) -> bool:
        """Whether validation found no errors (warnings remain visible)."""
        return not any(issue.level == "error" for issue in self.issues)


class ContractValidationResult[T: BaseModel](BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    value: T | None
    report: ValidationReport


__all__ = ["ContractValidationResult", "ValidationIssue", "ValidationReport"]
