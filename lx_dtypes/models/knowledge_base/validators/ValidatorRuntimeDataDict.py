"""Result contracts for report-template validator execution."""

from __future__ import annotations

from typing import Literal, TypedDict

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
    name: str
    ok: bool


class FindingsValidatorExecutionDataDict(TypedDict):
    name: str
    ok: bool
    operator: str
    finding: str
    matched_occurrences: int
    triggered_occurrences: int
    missing_required_classifications: list[str]
    issues: list[RuntimeValidationIssueDataDict]


class ClassificationValidatorExecutionDataDict(TypedDict):
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


class InterventionValidatorExecutionDataDict(TypedDict):
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


class UnitValidatorExecutionDataDict(TypedDict):
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


class ExaminationValidatorExecutionDataDict(TypedDict):
    name: str
    ok: bool
    finding_validator_status: list[ExaminationValidatorDependencyStatusDataDict]
    examination_validator_status: list[ExaminationValidatorDependencyStatusDataDict]
    issues: list[RuntimeValidationIssueDataDict]


class ReportTemplateRuntimeValidationResultDataDict(TypedDict):
    template_name: str
    ok: bool
    evaluated_findings_count: int
    classification_validators: list[ClassificationValidatorExecutionDataDict]
    intervention_validators: list[InterventionValidatorExecutionDataDict]
    findings_validators: list[FindingsValidatorExecutionDataDict]
    examination_validators: list[ExaminationValidatorExecutionDataDict]
    unit_validators: list[UnitValidatorExecutionDataDict]
    issues: list[RuntimeValidationIssueDataDict]
