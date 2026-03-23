from collections.abc import Mapping
from typing import List, Literal, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from lx_dtypes.factories import str_unknown_factory
from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.knowledge_base.report_template.ClassificationValidatorDataDict import (
    ClassificationValidatorConditionDataDict,
    ClassificationValidatorDataDict,
    ClassificationValidatorOperatorLiteral,
    ClassificationValidatorPrecedenceLiteral,
    ClassificationValidatorQueryDataDict,
)
from lx_dtypes.models.knowledge_base.report_template.ValidatorRequirementReference import (
    ValidatorRequirementReference,
)
from lx_dtypes.models.knowledge_base.report_template.FindingsValidator import (
    FindingsValidatorConditionClause,
    _normalize_value,
)
from lx_dtypes.models.knowledge_base.report_template.ValueTypes import ValidationParams

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


class ClassificationValidatorCondition(BaseModel):
    model_config = ConfigDict(extra="forbid")

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


class ClassificationValidatorQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

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

    @field_validator("condition", mode="before")
    @classmethod
    def normalize_condition(cls, value: object) -> object:
        return value

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
    def ddict(self) -> ClassificationValidatorQueryDataDict:
        return cast(
            ClassificationValidatorQueryDataDict, self.model_dump(mode="python")
        )


class ClassificationValidator(KnowledgebaseBaseModel[ClassificationValidatorDataDict]):
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
        if not isinstance(value, Mapping):
            return value
        data = dict(value)
        query_raw = data.get("query")
        query = dict(query_raw) if isinstance(query_raw, Mapping) else {}
        if "finding" not in data and "finding" in query:
            data["finding"] = query["finding"]
        if "classification" not in data and "classification" in query:
            data["classification"] = query["classification"]
        if "operator" not in data and "operator" in query:
            data["operator"] = query["operator"]
        if "finding" in data and "finding" not in query:
            query["finding"] = data["finding"]
        if "classification" in data and "classification" not in query:
            query["classification"] = data["classification"]
        if "operator" in data and "operator" not in query:
            query["operator"] = data["operator"]
        data["query"] = query
        return data

    @model_validator(mode="after")
    def validate_query_alignment(self) -> "ClassificationValidator":
        if self.query.finding is None:
            self.query.finding = self.finding
        if self.query.classification is None:
            self.query.classification = self.classification
        if self.query.finding != self.finding:
            raise ValueError(
                "query.finding must match the top-level `finding` value for a validator."
            )
        if self.query.classification != self.classification:
            raise ValueError(
                "query.classification must match the top-level `classification` value for a validator."
            )
        if self.query.operator != self.operator:
            raise ValueError(
                "query.operator must match the top-level `operator` value for a validator."
            )
        return self

    @classmethod
    def list_type_fields(cls) -> List[str]:
        return []

    @property
    def ddict_class(self) -> type[ClassificationValidatorDataDict]:
        return ClassificationValidatorDataDict
