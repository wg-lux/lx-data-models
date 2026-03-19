from typing import Any, Dict, List, Literal, TypedDict

from lx_dtypes.models.base.app_base_model.ddict.KnowledgebaseBaseModelDataDict import (
    KnowledgebaseBaseModelDataDict,
)
from lx_dtypes.models.knowledge_base.report_template.FindingsValidatorDataDict import (
    FindingsValidatorComparatorLiteral,
)
from lx_dtypes.models.knowledge_base.report_template.ValidatorRequirementReferenceDataDict import (
    ValidatorRequirementReferenceDataDict,
)

UnitValidatorOperatorLiteral = Literal["exists", "missing", "condition"]
UnitValidatorPrecedenceLiteral = Literal["required", "optional"]


class UnitValidatorConditionClauseDataDict(TypedDict, total=False):
    classification: str
    comparator: FindingsValidatorComparatorLiteral
    value: Any
    values: List[Any]


class UnitValidatorConditionDataDict(TypedDict, total=False):
    any: List[UnitValidatorConditionClauseDataDict]
    all: List[UnitValidatorConditionClauseDataDict]
    then_requires: List[ValidatorRequirementReferenceDataDict]


class UnitValidatorQueryDataDict(TypedDict, total=False):
    finding: str
    classification: str
    unit: str
    operator: UnitValidatorOperatorLiteral
    params: Dict[str, Any]
    condition: UnitValidatorConditionDataDict


class UnitValidatorHintDataDict(TypedDict, total=False):
    unit_name: str
    precedence: UnitValidatorPrecedenceLiteral
    abbreviation: str
    unit_types: List[str]


class UnitValidatorDataDict(KnowledgebaseBaseModelDataDict):
    query: UnitValidatorQueryDataDict
    finding: str
    classification: str
    unit: str
    operator: UnitValidatorOperatorLiteral
    precedence: UnitValidatorPrecedenceLiteral
