from typing import Literal, cast

from pydantic import Field, field_validator, model_validator

from lx_dtypes.factories import str_unknown_factory
from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.knowledge_base.validators.FindingsValidator import (
    FindingsValidatorConditionClause,
    _normalize_value,
)
from lx_dtypes.models.knowledge_base.validators.InterventionValidatorDataDict import (
    InterventionValidatorConditionDataDict,
    InterventionValidatorDataDict,
    InterventionValidatorOperatorLiteral,
    InterventionValidatorPrecedenceLiteral,
    InterventionValidatorQueryDataDict,
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
)
from lx_dtypes.models.model import DtypesModel

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


class InterventionValidatorCondition(DtypesModel):
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


class InterventionValidatorQuery(DtypesModel):
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
        validate_operator_condition(self.operator, self.condition)
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
        return normalize_query_defaults(
            value, InterventionValidatorQuery, ("finding", "intervention", "operator")
        )

    @model_validator(mode="after")
    def validate_query_alignment(self) -> "InterventionValidator":
        self.query = align_query(
            self.query,
            {
                "finding": self.finding,
                "intervention": self.intervention,
                "operator": self.operator,
            },
            suffix="",
        )
        return self

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return []

    @property
    def ddict_class(self) -> type[InterventionValidatorDataDict]:
        return InterventionValidatorDataDict
