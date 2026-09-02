from collections.abc import Mapping
from typing import Literal, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from lx_dtypes.factories import str_unknown_factory
from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.knowledge_base.report_template.FindingsValidator import (
    FindingsValidatorConditionClause,
    _normalize_value,
)
from lx_dtypes.models.knowledge_base.report_template.UnitValidatorDataDict import (
    UnitValidatorConditionDataDict,
    UnitValidatorDataDict,
    UnitValidatorOperatorLiteral,
    UnitValidatorPrecedenceLiteral,
    UnitValidatorQueryDataDict,
)
from lx_dtypes.models.knowledge_base.report_template.ValidatorRequirementReference import (
    ValidatorRequirementReference,
)
from lx_dtypes.models.knowledge_base.report_template.ValueTypes import ValidationParams

UnitValidatorOperator = Literal["exists", "missing", "condition"]
UnitValidatorPrecedence = Literal["required", "optional"]

UNIT_VALIDATOR_OPERATORS: tuple[UnitValidatorOperator, ...] = (
    "exists",
    "missing",
    "condition",
)
UNIT_VALIDATOR_PRECEDENCE: tuple[UnitValidatorPrecedence, ...] = (
    "required",
    "optional",
)


class UnitValidatorConditionClause(FindingsValidatorConditionClause):
    pass


class UnitValidatorCondition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    any: list[UnitValidatorConditionClause] = Field(default_factory=list)
    all: list[UnitValidatorConditionClause] = Field(default_factory=list)
    then_requires: list[ValidatorRequirementReference] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_branches(self) -> "UnitValidatorCondition":
        if len(self.any) == 0 and len(self.all) == 0:
            raise ValueError(
                "condition requires at least one clause in `any` or `all`."
            )
        return self

    @property
    def ddict(self) -> UnitValidatorConditionDataDict:
        return cast(UnitValidatorConditionDataDict, self.model_dump(mode="python"))


class UnitValidatorQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    finding: str | None = None
    classification: str | None = None
    unit: str | None = None
    operator: UnitValidatorOperatorLiteral = "exists"
    params: ValidationParams = Field(default_factory=dict)
    condition: UnitValidatorCondition | None = None

    @field_validator("operator", mode="before")
    @classmethod
    def normalize_operator(cls, value: object) -> object:
        return _normalize_value(
            value,
            field_name="unit_validator.operator",
            valid_values=UNIT_VALIDATOR_OPERATORS,
        )

    @model_validator(mode="after")
    def validate_operator_semantics(self) -> "UnitValidatorQuery":
        if self.operator == "condition":
            if self.condition is None:
                raise ValueError(
                    "operator 'condition' requires a populated `condition` block."
                )
            return self
        if self.condition is not None:
            raise ValueError(
                f"operator '{self.operator}' does not allow a `condition` block."
            )
        return self

    @property
    def ddict(self) -> UnitValidatorQueryDataDict:
        return cast(UnitValidatorQueryDataDict, self.model_dump(mode="python"))


class UnitValidator(KnowledgebaseBaseModel[UnitValidatorDataDict]):
    query: UnitValidatorQuery = Field(default_factory=UnitValidatorQuery)
    finding: str = Field(default_factory=str_unknown_factory)
    classification: str = Field(default_factory=str_unknown_factory)
    unit: str = Field(default_factory=str_unknown_factory)
    operator: UnitValidatorOperatorLiteral = "exists"
    precedence: UnitValidatorPrecedenceLiteral = "required"

    @field_validator("operator", mode="before")
    @classmethod
    def normalize_operator(cls, value: object) -> object:
        return _normalize_value(
            value,
            field_name="unit_validator.operator",
            valid_values=UNIT_VALIDATOR_OPERATORS,
        )

    @field_validator("precedence", mode="before")
    @classmethod
    def normalize_precedence(cls, value: object) -> object:
        return _normalize_value(
            value,
            field_name="unit_validator.precedence",
            valid_values=UNIT_VALIDATOR_PRECEDENCE,
        )

    @model_validator(mode="before")
    @classmethod
    def normalize_query_defaults(cls, value: object) -> object:
        if not isinstance(value, Mapping):
            return value
        data = dict(value)
        query_raw = data.get("query")
        query = dict(query_raw) if isinstance(query_raw, Mapping) else {}
        for field_name in ("finding", "classification", "unit", "operator"):
            if field_name not in data and field_name in query:
                data[field_name] = query[field_name]
            if field_name in data and field_name not in query:
                query[field_name] = data[field_name]
        data["query"] = query
        return data

    @model_validator(mode="after")
    def validate_query_alignment(self) -> "UnitValidator":
        if self.query.finding is None:
            self.query.finding = self.finding
        if self.query.classification is None:
            self.query.classification = self.classification
        if self.query.unit is None:
            self.query.unit = self.unit
        if self.query.finding != self.finding:
            raise ValueError("query.finding must match the top-level `finding` value.")
        if self.query.classification != self.classification:
            raise ValueError(
                "query.classification must match the top-level `classification` value."
            )
        if self.query.unit != self.unit:
            raise ValueError("query.unit must match the top-level `unit` value.")
        if self.query.operator != self.operator:
            raise ValueError(
                "query.operator must match the top-level `operator` value."
            )
        return self

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return []

    @property
    def ddict_class(self) -> type[UnitValidatorDataDict]:
        return UnitValidatorDataDict
