"""Transport contracts for advisory validation; findings never authorize writes."""

from typing import Literal

from pydantic import BaseModel, Field, computed_field

from lx_dtypes.models.model import FrozenContractModel

from .knowledge_base import KnowledgeBaseIdentity


class SemanticValidationError(ValueError):
    """Expected cross-model failure carrying a stable finding code."""

    def __init__(self, code: str, message: str | None = None) -> None:
        self.code = code
        super().__init__(message or code)


class ValidationIssue(FrozenContractModel):
    """Single finding produced by advisory validation.

    Attributes:
        code: Stable machine-readable code, for example
            ``"terminology.identity_mismatch"``.
        message: Localized description.
        level: ``"error"`` or ``"warning"``.
        source: Layer that produced the issue: the contract shape, the
            terminology, or the study rules.
        path: Location of the offending value within the payload.
        validator_name: Knowledge-base validator that reported the issue.
    """

    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    level: Literal["error", "warning"] = "error"
    source: Literal["contract", "terminology", "study"]
    path: tuple[str | int, ...] = ()
    validator_name: str | None = None


class ValidationReport(FrozenContractModel):
    """Collected issues of one validation run.

    Attributes:
        schema_version: Version of this report format.
        issues: All issues found, errors and warnings.
        knowledge_base_identity: Terminology version used for the checks.
        study_evaluated: Whether study rules were applied.
    """

    schema_version: Literal["1.0"] = "1.0"
    issues: tuple[ValidationIssue, ...] = ()
    knowledge_base_identity: KnowledgeBaseIdentity | None = None
    study_evaluated: bool = False

    @computed_field
    @property
    def ok(self) -> bool:
        """Whether validation found no errors (warnings remain visible)."""
        return not any(issue.level == "error" for issue in self.issues)


class ContractValidationResult[T: BaseModel](FrozenContractModel):
    """Typed value and report returned by non-raising contract validation.

    ``value`` holds the validated model only when the report contains no
    errors; otherwise it is ``None``.
    """

    value: T | None
    report: ValidationReport


__all__ = [
    "ContractValidationResult",
    "SemanticValidationError",
    "ValidationIssue",
    "ValidationReport",
]
