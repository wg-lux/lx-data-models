from collections.abc import Mapping
from typing import Literal, cast

from pydantic import Field, field_validator, model_validator

from lx_dtypes.factories import str_unknown_factory
from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.knowledge_base.validators.FindingsValidatorDataDict import (
    FindingsValidatorConditionDataDict,
    FindingsValidatorDataDict,
    FindingsValidatorOperatorLiteral,
    FindingsValidatorQueryDataDict,
)
from lx_dtypes.models.knowledge_base.validators.QueryNormalization import (
    align_query,
    normalize_query_defaults,
    validate_operator_condition,
)
from lx_dtypes.models.knowledge_base.validators.ValidatorRequirementReference import (
    ValidatorRequirementReference,
)
from lx_dtypes.models.knowledge_base.validators.ValueTypes import (
    ValidationParams,
    ValidationScalar,
)
from lx_dtypes.models.model import DtypesModel

FindingsValidatorOperator = Literal[
    "exists",
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
    "not_in",
    "exists",
    "present",
]

FINDINGS_VALIDATOR_OPERATORS: tuple[FindingsValidatorOperator, ...] = (
    "exists",
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
    "not_in",
    "exists",
    "present",
)

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


def _normalize_value(
    raw_value: object,
    *,
    field_name: str,
    valid_values: tuple[str, ...],
) -> str:
    normalized = str(raw_value).strip().lower()
    if not normalized:
        raise ValueError(f"{field_name} cannot be empty")
    if normalized in valid_values:
        return normalized
    allowed = ", ".join(valid_values)
    raise ValueError(f"Unsupported {field_name} '{raw_value}'. Allowed: {allowed}")


def _normalize_value_with_alias(
    raw_value: object,
    *,
    field_name: str,
    valid_values: tuple[str, ...],
    deprecated_aliases: Mapping[str, str],
) -> str:
    normalized = str(raw_value).strip().lower()
    if not normalized:
        raise ValueError(f"{field_name} cannot be empty")
    if normalized in valid_values:
        return normalized
    if normalized in deprecated_aliases:
        canonical = deprecated_aliases[normalized]
        raise ValueError(
            f"Deprecated {field_name} alias '{raw_value}' is no longer supported; "
            f"use '{canonical}' instead."
        )
    allowed = ", ".join(valid_values)
    raise ValueError(f"Unsupported {field_name} '{raw_value}'. Allowed: {allowed}")


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


class FindingsValidatorConditionClause(DtypesModel):
    classification: str
    comparator: FindingsValidatorComparatorLiteral = "eq"
    value: ValidationScalar | None = None
    values: list[ValidationScalar] | None = None

    @field_validator("comparator", mode="before")
    @classmethod
    def normalize_comparator(cls, value: object) -> object:
        return _normalize_value_with_alias(
            value,
            field_name="findings_validator.comparator",
            valid_values=FINDINGS_VALIDATOR_COMPARATORS,
            deprecated_aliases=DEPRECATED_FINDINGS_VALIDATOR_COMPARATOR_ALIASES,
        )

    @model_validator(mode="after")
    def validate_comparator_payload(self) -> "FindingsValidatorConditionClause":
        if self.comparator in {"in", "not_in"}:
            if self.values is None:
                if self.value is None:
                    raise ValueError(
                        "comparators 'in' and 'not_in' require `values` (or `value`)."
                    )
                self.values = [self.value]
            if len(self.values) == 0:
                raise ValueError(
                    "comparators 'in' and 'not_in' require a non-empty `values` list."
                )
            return self

        if self.value is None:
            raise ValueError(f"comparator '{self.comparator}' requires `value`.")
        return self

    @property
    def expected_values(self) -> tuple[ValidationScalar, ...]:
        """Dynamically normalizes value/values into a unified tuple."""
        if self.values:
            return tuple(self.values)
        if self.value is not None:
            return (self.value,)
        return ()


class FindingsValidatorRequiredClassification(DtypesModel):
    classification: str


class FindingsValidatorCondition(DtypesModel):
    any: list[FindingsValidatorConditionClause] = Field(default_factory=list)
    all: list[FindingsValidatorConditionClause] = Field(default_factory=list)
    then_requires: list[ValidatorRequirementReference] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_branches(self) -> "FindingsValidatorCondition":
        if len(self.any) == 0 and len(self.all) == 0:
            raise ValueError(
                "condition requires at least one clause in `any` or `all`."
            )
        return self

    @property
    def ddict(self) -> FindingsValidatorConditionDataDict:
        return cast(FindingsValidatorConditionDataDict, self.model_dump(mode="python"))


class FindingsValidatorQuery(DtypesModel):
    finding: str | None = None
    operator: FindingsValidatorOperatorLiteral = "exists"
    params: ValidationParams = Field(default_factory=dict)
    condition: FindingsValidatorCondition | None = None

    @field_validator("operator", mode="before")
    @classmethod
    def normalize_operator(cls, value: object) -> object:
        return _normalize_value(
            value,
            field_name="findings_validator.operator",
            valid_values=FINDINGS_VALIDATOR_OPERATORS,
        )

    @model_validator(mode="after")
    def validate_operator_semantics(self) -> "FindingsValidatorQuery":
        validate_operator_condition(self.operator, self.condition)
        return self

    @property
    def ddict(self) -> FindingsValidatorQueryDataDict:
        return cast(FindingsValidatorQueryDataDict, self.model_dump(mode="python"))


class FindingsValidator(KnowledgebaseBaseModel[FindingsValidatorDataDict]):
    """Knowledge-base rule that checks whether a finding was reported.

    Attributes:
        query: Optional sub-query restricting which occurrences are checked.
        finding: Name of the finding to look for.
        operator: ``"exists"`` requires at least one occurrence, ``"missing"``
            requires none, and ``"condition"`` evaluates the query's condition
            on each occurrence.
    """

    query: FindingsValidatorQuery = Field(default_factory=FindingsValidatorQuery)
    finding: str = Field(default_factory=str_unknown_factory)
    operator: FindingsValidatorOperatorLiteral = "exists"

    @field_validator("operator", mode="before")
    @classmethod
    def normalize_operator(cls, value: object) -> object:
        return _normalize_value(
            value,
            field_name="findings_validator.operator",
            valid_values=FINDINGS_VALIDATOR_OPERATORS,
        )

    @model_validator(mode="before")
    @classmethod
    def normalize_query_defaults(cls, value: object) -> object:
        return normalize_query_defaults(
            value, FindingsValidatorQuery, ("finding", "operator")
        )

    @model_validator(mode="after")
    def validate_query_alignment(self) -> "FindingsValidator":
        self.query = align_query(
            self.query,
            {"finding": self.finding, "operator": self.operator},
            suffix=" for a validator",
        )
        return self

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return []

    @property
    def ddict_class(self) -> type[FindingsValidatorDataDict]:
        return FindingsValidatorDataDict
