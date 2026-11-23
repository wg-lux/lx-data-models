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
from lx_dtypes.models.knowledge_base.validators.QueryNormalization import (
    align_query,
    normalize_query_defaults,
    validate_operator_condition,
)
from lx_dtypes.models.knowledge_base.validators.UnitValidatorDataDict import (
    UnitValidatorConditionDataDict,
    UnitValidatorDataDict,
    UnitValidatorOperatorLiteral,
    UnitValidatorPrecedenceLiteral,
    UnitValidatorQueryDataDict,
)
from lx_dtypes.models.knowledge_base.validators.ValidatorRequirementReference import (
    ValidatorRequirementReference,
)
from lx_dtypes.models.knowledge_base.validators.ValueTypes import (
    ValidationParams,
)
from lx_dtypes.models.model import DtypesModel

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


class UnitValidatorCondition(DtypesModel):
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


class UnitValidatorQuery(DtypesModel):
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
        validate_operator_condition(self.operator, self.condition)
        return self

    @property
    def ddict(self) -> UnitValidatorQueryDataDict:
        return cast(UnitValidatorQueryDataDict, self.model_dump(mode="python"))


class UnitValidator(KnowledgebaseBaseModel[UnitValidatorDataDict]):
    """Knowledge-base rule that checks the unit of a classification value.

    Attributes:
        query: Optional sub-query with a condition on the occurrence.
        finding: Name of the finding whose occurrences are checked.
        classification: Classification whose descriptor value is checked.
        unit: Expected unit name.
        operator: ``"exists"``, ``"missing"``, or ``"condition"``.
        precedence: ``"optional"`` or ``"required"``; see
            :class:`ClassificationValidator`.
    """

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
        return normalize_query_defaults(
            value, UnitValidatorQuery, ("finding", "classification", "unit", "operator")
        )

    @model_validator(mode="after")
    def validate_query_alignment(self) -> "UnitValidator":
        self.query = align_query(
            self.query,
            {
                "finding": self.finding,
                "classification": self.classification,
                "unit": self.unit,
                "operator": self.operator,
            },
            suffix="",
        )
        return self

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return []

    @property
    def ddict_class(self) -> type[UnitValidatorDataDict]:
        return UnitValidatorDataDict
