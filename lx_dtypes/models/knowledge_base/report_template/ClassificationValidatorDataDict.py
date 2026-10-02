from typing import Literal, NotRequired, TypedDict

from lx_dtypes.models.base.app_base_model.ddict.KnowledgebaseBaseModelDataDict import (
    KnowledgebaseBaseModelDataDict,
)
from lx_dtypes.models.knowledge_base.report_template.FindingsValidatorDataDict import (
    FindingsValidatorComparatorLiteral,
)
from lx_dtypes.models.knowledge_base.report_template.ValidatorRequirementReferenceDataDict import (
    ValidatorRequirementReferenceDataDict,
)
from lx_dtypes.models.knowledge_base.report_template.ValueTypes import (
    ValidationParams,
    ValidationScalar,
)

ClassificationValidatorOperatorLiteral = Literal["exists", "missing", "condition"]
ClassificationValidatorPrecedenceLiteral = Literal["required", "optional"]
ClassificationValidatorHintDataTypeLiteral = Literal[
    "binary",
    "non_categorical",
    "ordered",
    "unknown",
]


class ClassificationValidatorConditionClauseDataDict(TypedDict, total=False):
    classification: str
    comparator: FindingsValidatorComparatorLiteral
    value: ValidationScalar
    values: list[ValidationScalar]


class ClassificationValidatorConditionDataDict(TypedDict, total=False):
    any: list[ClassificationValidatorConditionClauseDataDict]
    all: list[ClassificationValidatorConditionClauseDataDict]
    then_requires: list[ValidatorRequirementReferenceDataDict]


class ClassificationValidatorQueryDataDict(TypedDict, total=False):
    finding: str
    classification: str
    operator: ClassificationValidatorOperatorLiteral
    params: ValidationParams
    condition: ClassificationValidatorConditionDataDict


class ClassificationValidatorHintDataDict(TypedDict):
    classification_name: str
    precedence: ClassificationValidatorPrecedenceLiteral
    data_type_hint: ClassificationValidatorHintDataTypeLiteral
    choice_names: NotRequired[list[str]]
    descriptor_types: NotRequired[list[str]]
    allows_multiple: NotRequired[bool]


class ClassificationValidatorDataDict(KnowledgebaseBaseModelDataDict):
    query: ClassificationValidatorQueryDataDict
    finding: str
    classification: str
    operator: ClassificationValidatorOperatorLiteral
    precedence: ClassificationValidatorPrecedenceLiteral
