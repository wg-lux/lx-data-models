from typing import Literal, cast

from pydantic import Field, field_validator, model_validator

from lx_dtypes.factories import str_unknown_factory
from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.knowledge_base.validators.ClassificationValidatorDataDict import (
    ClassificationValidatorConditionDataDict,
    ClassificationValidatorDataDict,
    ClassificationValidatorOperatorLiteral,
    ClassificationValidatorPrecedenceLiteral,
    ClassificationValidatorQueryDataDict,
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
from lx_dtypes.models.knowledge_base.validators.ValidatorRequirementReference import (
    ValidatorRequirementReference,
)
from lx_dtypes.models.knowledge_base.validators.ValueTypes import (
    ValidationParams,
)
from lx_dtypes.models.model import DtypesModel

ClassificationValidatorOperator = Literal["exists", "missing", "condition"]
ClassificationValidatorPrecedence = Literal["required", "optional"]

CLASSIFICATION_VALIDATOR_OPERATORS: tuple[ClassificationValidatorOperator, ...] = (
    "exists",
    "missing",
    "condition",
)
CLASSIFICATION_VALIDATOR_PRECEDENCE: tuple[ClassificationValidatorPrecedence, ...] = (
    "required",
    "optional",
)


class ClassificationValidatorConditionClause(FindingsValidatorConditionClause):
    pass


class ClassificationValidatorCondition(DtypesModel):
    any: list[ClassificationValidatorConditionClause] = Field(default_factory=list)
    all: list[ClassificationValidatorConditionClause] = Field(default_factory=list)
    then_requires: list[ValidatorRequirementReference] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_branches(self) -> "ClassificationValidatorCondition":
        if len(self.any) == 0 and len(self.all) == 0:
            raise ValueError(
                "condition requires at least one clause in `any` or `all`."
            )
        return self

    @property
    def ddict(self) -> ClassificationValidatorConditionDataDict:
        return cast(
            ClassificationValidatorConditionDataDict, self.model_dump(mode="python")
        )


class ClassificationValidatorQuery(DtypesModel):
    finding: str | None = None
    classification: str | None = None
    operator: ClassificationValidatorOperatorLiteral = "exists"
    params: ValidationParams = Field(default_factory=dict)
    condition: ClassificationValidatorCondition | None = None

    @field_validator("operator", mode="before")
    @classmethod
    def normalize_operator(cls, value: object) -> object:
        return _normalize_value(
            value,
            field_name="classification_validator.operator",
            valid_values=CLASSIFICATION_VALIDATOR_OPERATORS,
        )

    @field_validator("classification", mode="before")
    @classmethod
    def normalize_classification(cls, value: object) -> object:
        if value is None:
            return value
        token = str(value).strip()
        if not token:
            raise ValueError("classification_validator.classification cannot be empty")
        return token

    @field_validator("finding", mode="before")
    @classmethod
    def normalize_finding(cls, value: object) -> object:
        if value is None:
            return value
        token = str(value).strip()
        if not token:
            raise ValueError("classification_validator.finding cannot be empty")
        return token

    @model_validator(mode="after")
    def validate_operator_semantics(self) -> "ClassificationValidatorQuery":
        validate_operator_condition(self.operator, self.condition)
        return self

    @property
    def ddict(self) -> ClassificationValidatorQueryDataDict:
        return cast(
            ClassificationValidatorQueryDataDict, self.model_dump(mode="python")
        )


class ClassificationValidator(KnowledgebaseBaseModel[ClassificationValidatorDataDict]):
    """Knowledge-base rule that checks a classification on a reported finding.

    Attributes:
        query: Optional sub-query with a condition on the occurrence.
        finding: Name of the finding whose occurrences are checked.
        classification: Classification that must carry a value.
        operator: ``"exists"``, ``"missing"``, or ``"condition"``.
        precedence: With ``"optional"``, the rule passes when the finding was
            not reported at all; with ``"required"``, an absent finding fails.
    """

    query: ClassificationValidatorQuery = Field(
        default_factory=ClassificationValidatorQuery
    )
    finding: str = Field(default_factory=str_unknown_factory)
    classification: str = Field(default_factory=str_unknown_factory)
    operator: ClassificationValidatorOperatorLiteral = "exists"
    precedence: ClassificationValidatorPrecedenceLiteral = "required"

    @field_validator("operator", mode="before")
    @classmethod
    def normalize_operator(cls, value: object) -> object:
        return _normalize_value(
            value,
            field_name="classification_validator.operator",
            valid_values=CLASSIFICATION_VALIDATOR_OPERATORS,
        )

    @field_validator("precedence", mode="before")
    @classmethod
    def normalize_precedence(cls, value: object) -> object:
        return _normalize_value(
            value,
            field_name="classification_validator.precedence",
            valid_values=CLASSIFICATION_VALIDATOR_PRECEDENCE,
        )

    @model_validator(mode="before")
    @classmethod
    def normalize_query_defaults(cls, value: object) -> object:
        return normalize_query_defaults(
            value,
            ClassificationValidatorQuery,
            ("finding", "classification", "operator"),
        )

    @model_validator(mode="after")
    def validate_query_alignment(self) -> "ClassificationValidator":
        self.query = align_query(
            self.query,
            {
                "finding": self.finding,
                "classification": self.classification,
                "operator": self.operator,
            },
            suffix=" for a validator",
        )
        return self

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return []

    @property
    def ddict_class(self) -> type[ClassificationValidatorDataDict]:
        return ClassificationValidatorDataDict
