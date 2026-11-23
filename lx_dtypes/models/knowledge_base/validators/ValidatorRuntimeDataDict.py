"""Result contracts for report-template validator execution."""

from __future__ import annotations

from typing import Literal, NotRequired, TypedDict

from lx_dtypes.models.knowledge_base.validators.ClassificationValidatorDataDict import (
    ClassificationValidatorHintDataDict,
)
from lx_dtypes.models.knowledge_base.validators.InterventionValidatorDataDict import (
    InterventionValidatorHintDataDict,
)
from lx_dtypes.models.knowledge_base.validators.UnitValidatorDataDict import (
    UnitValidatorHintDataDict,
)
from lx_dtypes.models.knowledge_base.validators.ValueTypes import (
    ValidationIssueDetails,
)


class RuntimeValidationIssueDataDict(TypedDict):
    """Issue reported by a validator during runtime evaluation.

    ``level`` is ``"error"`` for violated rules and ``"warning"`` when the
    data needed to evaluate a condition is missing.
    """

    code: str
    level: Literal["error", "warning"]
    message: str
    validator_name: str
    validator_kind: Literal[
        "classification_validator",
        "intervention_validator",
        "findings_validator",
        "examination_validator",
        "template",
        "unit_validator",
    ]
    details: ValidationIssueDetails


class ExaminationValidatorDependencyStatusDataDict(TypedDict):
    """Pass/fail status of one validator referenced by an examination validator."""

    name: str
    ok: bool


class FindingsValidatorExecutionDataDict(TypedDict):
    """Result of evaluating one :class:`FindingsValidator`.

    ``matched_occurrences`` counts reported occurrences of the finding, and
    ``triggered_occurrences`` counts those whose condition applied.
    """

    name: str
    ok: bool
    operator: str
    finding: str
    matched_occurrences: int
    triggered_occurrences: int
    missing_required_classifications: list[str]
    issues: list[RuntimeValidationIssueDataDict]
    # Identifier -> display name in the requested language for this entry's
    # validator and referenced concepts; identifiers without a translation map to themselves.
    display_names: NotRequired[dict[str, str]]


class ClassificationValidatorExecutionDataDict(TypedDict):
    """Result of evaluating one :class:`ClassificationValidator`.

    ``hint`` describes the expected value shape so a UI can prompt for it.
    """

    name: str
    ok: bool
    operator: str
    finding: str
    classification: str
    precedence: Literal["required", "optional"]
    matched_occurrences: int
    triggered_occurrences: int
    hint: ClassificationValidatorHintDataDict
    issues: list[RuntimeValidationIssueDataDict]
    # Identifier -> display name in the requested language for this entry's
    # validator and referenced concepts; identifiers without a translation map to themselves.
    display_names: NotRequired[dict[str, str]]


class InterventionValidatorExecutionDataDict(TypedDict):
    """Result of evaluating one :class:`InterventionValidator`."""

    name: str
    ok: bool
    operator: str
    finding: str
    intervention: str
    precedence: Literal["required", "optional"]
    matched_occurrences: int
    triggered_occurrences: int
    hint: InterventionValidatorHintDataDict
    issues: list[RuntimeValidationIssueDataDict]
    # Identifier -> display name in the requested language for this entry's
    # validator and referenced concepts; identifiers without a translation map to themselves.
    display_names: NotRequired[dict[str, str]]


class UnitValidatorExecutionDataDict(TypedDict):
    """Result of evaluating one :class:`UnitValidator`."""

    name: str
    ok: bool
    operator: str
    finding: str
    classification: str
    unit: str
    precedence: Literal["required", "optional"]
    matched_occurrences: int
    triggered_occurrences: int
    hint: UnitValidatorHintDataDict
    issues: list[RuntimeValidationIssueDataDict]
    # Identifier -> display name in the requested language for this entry's
    # validator and referenced concepts; identifiers without a translation map to themselves.
    display_names: NotRequired[dict[str, str]]


class ExaminationValidatorExecutionDataDict(TypedDict):
    """Result of evaluating one :class:`ExaminationValidator` and its dependencies."""

    name: str
    ok: bool
    finding_validator_status: list[ExaminationValidatorDependencyStatusDataDict]
    examination_validator_status: list[ExaminationValidatorDependencyStatusDataDict]
    issues: list[RuntimeValidationIssueDataDict]
    # Identifier -> display name in the requested language for this entry's
    # validator and referenced concepts; identifiers without a translation map to themselves.
    display_names: NotRequired[dict[str, str]]


class ReportTemplateRuntimeValidationResultDataDict(TypedDict):
    """Combined result of all validators of one report template.

    ``ok`` is ``True`` only when every validator passed. ``issues`` collects
    the issues of all validators.
    """

    template_name: str
    ok: bool
    evaluated_findings_count: int
    classification_validators: list[ClassificationValidatorExecutionDataDict]
    intervention_validators: list[InterventionValidatorExecutionDataDict]
    findings_validators: list[FindingsValidatorExecutionDataDict]
    examination_validators: list[ExaminationValidatorExecutionDataDict]
    unit_validators: list[UnitValidatorExecutionDataDict]
    issues: list[RuntimeValidationIssueDataDict]
    # Identifier -> display name in the requested language for this entry's
    # validator and referenced concepts; identifiers without a translation map to themselves.
    display_names: NotRequired[dict[str, str]]
