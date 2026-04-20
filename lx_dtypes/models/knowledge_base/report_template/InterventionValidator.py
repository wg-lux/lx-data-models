from collections.abc import Mapping
from typing import List, Literal, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from lx_dtypes.factories import str_unknown_factory
from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.knowledge_base.report_template.FindingsValidator import (
    FindingsValidatorConditionClause,
    _normalize_value,
)
from lx_dtypes.models.knowledge_base.report_template.InterventionValidatorDataDict import (
    InterventionValidatorConditionDataDict,
    InterventionValidatorDataDict,
    InterventionValidatorOperatorLiteral,
    InterventionValidatorPrecedenceLiteral,
    InterventionValidatorQueryDataDict,
)
from lx_dtypes.models.knowledge_base.report_template.ValidatorRequirementReference import (
    ValidatorRequirementReference,
)
from lx_dtypes.models.knowledge_base.report_template.ValueTypes import ValidationParams

InterventionValidatorOperator = Literal["exists", "missing", "condition"]
InterventionValidatorPrecedence = Literal["required", "optional"]

INTERVENTION_VALIDATOR_OPERATORS: tuple[InterventionValidatorOperator, ...] = (
    "exists",
    "missing",
    "condition",
)
INTERVENTION_VALIDATOR_PRECEDENCE: tuple[InterventionValidatorPrecedence, ...] = (
    "required",
    "optional",
)


class InterventionValidatorConditionClause(FindingsValidatorConditionClause):
    pass


class InterventionValidatorCondition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    any: list[InterventionValidatorConditionClause] = Field(default_factory=list)
    all: list[InterventionValidatorConditionClause] = Field(default_factory=list)
    then_requires: list[ValidatorRequirementReference] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_branches(self) -> "InterventionValidatorCondition":
        if len(self.any) == 0 and len(self.all) == 0:
            raise ValueError(
                "condition requires at least one clause in `any` or `all`."
            )
        return self

    @property
    def ddict(self) -> InterventionValidatorConditionDataDict:
        return cast(
            InterventionValidatorConditionDataDict, self.model_dump(mode="python")
        )


class InterventionValidatorQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    finding: str | None = None
    intervention: str | None = None
    operator: InterventionValidatorOperatorLiteral = "exists"
    params: ValidationParams = Field(default_factory=dict)
    condition: InterventionValidatorCondition | None = None

    @field_validator("operator", mode="before")
    @classmethod
    def normalize_operator(cls, value: object) -> object:
        return _normalize_value(
            value,
            field_name="intervention_validator.operator",
            valid_values=INTERVENTION_VALIDATOR_OPERATORS,
        )

    @model_validator(mode="after")
    def validate_operator_semantics(self) -> "InterventionValidatorQuery":
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
    def ddict(self) -> InterventionValidatorQueryDataDict:
        return cast(InterventionValidatorQueryDataDict, self.model_dump(mode="python"))


class InterventionValidator(KnowledgebaseBaseModel[InterventionValidatorDataDict]):
    query: InterventionValidatorQuery = Field(
        default_factory=InterventionValidatorQuery
    )
    finding: str = Field(default_factory=str_unknown_factory)
    intervention: str = Field(default_factory=str_unknown_factory)
    operator: InterventionValidatorOperatorLiteral = "exists"
    precedence: InterventionValidatorPrecedenceLiteral = "required"

    @field_validator("operator", mode="before")
    @classmethod
    def normalize_operator(cls, value: object) -> object:
        return _normalize_value(
            value,
            field_name="intervention_validator.operator",
            valid_values=INTERVENTION_VALIDATOR_OPERATORS,
        )

    @field_validator("precedence", mode="before")
    @classmethod
    def normalize_precedence(cls, value: object) -> object:
        return _normalize_value(
            value,
            field_name="intervention_validator.precedence",
            valid_values=INTERVENTION_VALIDATOR_PRECEDENCE,
        )

    @model_validator(mode="before")
    @classmethod
    def normalize_query_defaults(cls, value: object) -> object:
        if not isinstance(value, Mapping):
            return value
        data = dict(value)
        query_raw = data.get("query")
        query = dict(query_raw) if isinstance(query_raw, Mapping) else {}
        for field_name in ("finding", "intervention", "operator"):
            if field_name not in data and field_name in query:
                data[field_name] = query[field_name]
            if field_name in data and field_name not in query:
                query[field_name] = data[field_name]
        data["query"] = query
        return data

    @model_validator(mode="after")
    def validate_query_alignment(self) -> "InterventionValidator":
        if self.query.finding is None:
            self.query.finding = self.finding
        if self.query.intervention is None:
            self.query.intervention = self.intervention
        if self.query.finding != self.finding:
            raise ValueError("query.finding must match the top-level `finding` value.")
        if self.query.intervention != self.intervention:
            raise ValueError(
                "query.intervention must match the top-level `intervention` value."
            )
        if self.query.operator != self.operator:
            raise ValueError(
                "query.operator must match the top-level `operator` value."
            )
        return self

    @classmethod
    def list_type_fields(cls) -> List[str]:
        return []

    @property
    def ddict_class(self) -> type[InterventionValidatorDataDict]:
        return InterventionValidatorDataDict
