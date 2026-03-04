from __future__ import annotations

import warnings
from typing import Any, Dict, List, Literal, TypedDict, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

FindingsValidatorOperator = Literal[
    "exists",
    "present",
    "not_exists",
    "absent",
    "missing",
    "condition",
]
FindingsValidatorComparator = Literal[
    "eq",
    "ne",
    "gt",
    "gte",
    "lt",
    "lte",
    "in",
    "exists",
    "present",
]

FINDINGS_VALIDATOR_OPERATORS: tuple[FindingsValidatorOperator, ...] = (
    "exists",
    "present",
    "not_exists",
    "absent",
    "missing",
    "condition",
)
FINDINGS_VALIDATOR_COMPARATORS: tuple[FindingsValidatorComparator, ...] = (
    "eq",
    "ne",
    "gt",
    "gte",
    "lt",
    "lte",
    "in",
    "exists",
    "present",
)

DEPRECATED_FINDINGS_VALIDATOR_OPERATOR_ALIASES: dict[str, FindingsValidatorOperator] = {
    "if": "condition",
    "not-exists": "not_exists",
    "not exists": "not_exists",
}
DEPRECATED_FINDINGS_VALIDATOR_COMPARATOR_ALIASES: dict[
    str, FindingsValidatorComparator
] = {
    "==": "eq",
    "!=": "ne",
    ">": "gt",
    ">=": "gte",
    "<": "lt",
    "<=": "lte",
}


class DeprecatedReportTemplateValueWarning(UserWarning):
    pass


def _normalize_value_with_alias(
    raw_value: Any,
    *,
    field_name: str,
    valid_values: tuple[str, ...],
    deprecated_aliases: dict[str, str],
) -> str:
    normalized = str(raw_value).strip().lower()
    if not normalized:
        raise ValueError(f"{field_name} cannot be empty")
    if normalized in valid_values:
        return normalized
    if normalized in deprecated_aliases:
        canonical = deprecated_aliases[normalized]
        warnings.warn(
            (
                f"Deprecated {field_name} alias '{raw_value}' detected; "
                f"use '{canonical}' instead."
            ),
            DeprecatedReportTemplateValueWarning,
            stacklevel=3,
        )
        return canonical
    allowed = ", ".join(valid_values)
    raise ValueError(f"Unsupported {field_name} '{raw_value}'. Allowed: {allowed}")


class ReportTemplateClassificationRequirementDataDict(TypedDict):
    classification: str
    required: bool


class ReportTemplateFindingRequirementDataDict(TypedDict):
    finding: str
    required: bool
    multiple_allowed: bool
    classifications: List[ReportTemplateClassificationRequirementDataDict]


class ReportTemplateValidatorsDataDict(TypedDict):
    examination_validators: List[str]
    findings_validators: List[str]


FindingsValidatorOperatorLiteral = Literal["exists", "missing", "conditional"]
FindingsValidatorComparatorLiteral = Literal[
    "eq",
    "ne",
    "gt",
    "gte",
    "lt",
    "lte",
    "in",
    "not_in",
]


class FindingsValidatorConditionClauseDataDict(TypedDict, total=False):
    classification: str
    comparator: FindingsValidatorComparatorLiteral
    value: Any
    values: List[Any]


class FindingsValidatorConditionDataDict(TypedDict, total=False):
    any: List[FindingsValidatorConditionClauseDataDict]
    all: List[FindingsValidatorConditionClauseDataDict]
    then_requires: List[Dict[str, Any]]


class FindingsValidatorQueryDataDict(TypedDict, total=False):
    finding: str
    operator: str
    params: Dict[str, Any]
    condition: FindingsValidatorConditionDataDict


class ReportTemplateSectionFieldDataDict(TypedDict, total=False):
    key: str
    required: bool
    label: str
    source: Literal["patient", "patient_examination", "history"]


class ReportTemplateClassificationRequirement(BaseModel):
    classification: str
    required: bool = False


class ReportTemplateFindingRequirement(BaseModel):
    finding: str
    required: bool = False
    multiple_allowed: bool = False
    classifications: List[ReportTemplateClassificationRequirement] = Field(
        default_factory=list
    )


class ReportTemplateValidators(BaseModel):
    examination_validators: List[str] = Field(default_factory=list)
    findings_validators: List[str] = Field(default_factory=list)


class FindingsValidatorConditionRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    classification: str
    comparator: FindingsValidatorComparator = "eq"
    value: Any | None = None

    @field_validator("comparator", mode="before")
    @classmethod
    def normalize_comparator(cls, value: Any) -> Any:
        return _normalize_value_with_alias(
            value,
            field_name="findings_validator.comparator",
            valid_values=FINDINGS_VALIDATOR_COMPARATORS,
            deprecated_aliases=DEPRECATED_FINDINGS_VALIDATOR_COMPARATOR_ALIASES,
        )


class FindingsValidatorRequiredClassification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    classification: str


class FindingsValidatorCondition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    any: List[FindingsValidatorConditionRule] = Field(default_factory=list)
    all: List[FindingsValidatorConditionRule] = Field(default_factory=list)
    then_requires: List[FindingsValidatorRequiredClassification] = Field(
        default_factory=list
    )


class FindingsValidatorQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    finding: str | None = None
    operator: FindingsValidatorOperator | None = None
    params: Dict[str, Any] = Field(default_factory=dict)
    condition: FindingsValidatorCondition | None = None

    @field_validator("operator", mode="before")
    @classmethod
    def normalize_operator(cls, value: Any) -> Any:
        if value is None:
            return None
        return _normalize_value_with_alias(
            value,
            field_name="findings_validator.operator",
            valid_values=FINDINGS_VALIDATOR_OPERATORS,
            deprecated_aliases=DEPRECATED_FINDINGS_VALIDATOR_OPERATOR_ALIASES,
        )


class ReportTemplateSectionField(BaseModel):
    key: str
    required: bool = False
    label: str | None = None
    source: Literal["patient", "patient_examination", "history"] | None = None


ReportTemplateFindingRequirementInput = Union[
    ReportTemplateFindingRequirement,
    str,
]
