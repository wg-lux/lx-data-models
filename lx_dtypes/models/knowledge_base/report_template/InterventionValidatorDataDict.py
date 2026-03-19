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

InterventionValidatorOperatorLiteral = Literal["exists", "missing", "condition"]
InterventionValidatorPrecedenceLiteral = Literal["required", "optional"]


class InterventionValidatorConditionClauseDataDict(TypedDict, total=False):
    classification: str
    comparator: FindingsValidatorComparatorLiteral
    value: Any
    values: List[Any]


class InterventionValidatorConditionDataDict(TypedDict, total=False):
    any: List[InterventionValidatorConditionClauseDataDict]
    all: List[InterventionValidatorConditionClauseDataDict]
    then_requires: List[ValidatorRequirementReferenceDataDict]


class InterventionValidatorQueryDataDict(TypedDict, total=False):
    finding: str
    intervention: str
    operator: InterventionValidatorOperatorLiteral
    params: Dict[str, Any]
    condition: InterventionValidatorConditionDataDict


class InterventionValidatorHintDataDict(TypedDict, total=False):
    intervention_name: str
    precedence: InterventionValidatorPrecedenceLiteral
    intervention_types: List[str]


class InterventionValidatorDataDict(KnowledgebaseBaseModelDataDict):
    query: InterventionValidatorQueryDataDict
    finding: str
    intervention: str
    operator: InterventionValidatorOperatorLiteral
    precedence: InterventionValidatorPrecedenceLiteral
