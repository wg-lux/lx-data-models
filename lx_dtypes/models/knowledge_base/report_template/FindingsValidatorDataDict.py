from typing import List, Literal, TypedDict

from lx_dtypes.models.base.app_base_model.ddict.KnowledgebaseBaseModelDataDict import (
    KnowledgebaseBaseModelDataDict,
)
from lx_dtypes.models.knowledge_base.report_template.ValidatorRequirementReferenceDataDict import (
    ValidatorRequirementReferenceDataDict,
)
from lx_dtypes.models.knowledge_base.report_template.ValueTypes import (
    ValidationParams,
    ValidationScalar,
)

FindingsValidatorOperatorLiteral = Literal["exists", "missing", "condition"]
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
    value: ValidationScalar
    values: List[ValidationScalar]


class FindingsValidatorConditionDataDict(TypedDict, total=False):
    any: List[FindingsValidatorConditionClauseDataDict]
    all: List[FindingsValidatorConditionClauseDataDict]
    then_requires: List[ValidatorRequirementReferenceDataDict]


class FindingsValidatorQueryDataDict(TypedDict, total=False):
    finding: str
    operator: str
    params: ValidationParams
    condition: FindingsValidatorConditionDataDict


class FindingsValidatorDataDict(KnowledgebaseBaseModelDataDict):
    query: FindingsValidatorQueryDataDict
    finding: str
    operator: FindingsValidatorOperatorLiteral
