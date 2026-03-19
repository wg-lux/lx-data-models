from typing import Any, Dict, List, Literal, TypedDict

from lx_dtypes.models.base.app_base_model.ddict.KnowledgebaseBaseModelDataDict import (
    KnowledgebaseBaseModelDataDict,
)
from lx_dtypes.models.knowledge_base.report_template.ValidatorRequirementReferenceDataDict import (
    ValidatorRequirementReferenceDataDict,
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
    value: Any
    values: List[Any]


class FindingsValidatorConditionDataDict(TypedDict, total=False):
    any: List[FindingsValidatorConditionClauseDataDict]
    all: List[FindingsValidatorConditionClauseDataDict]
    then_requires: List[ValidatorRequirementReferenceDataDict]


class FindingsValidatorQueryDataDict(TypedDict, total=False):
    finding: str
    operator: str
    params: Dict[str, Any]
    condition: FindingsValidatorConditionDataDict


class FindingsValidatorDataDict(KnowledgebaseBaseModelDataDict):
    query: FindingsValidatorQueryDataDict
    finding: str
    operator: FindingsValidatorOperatorLiteral
