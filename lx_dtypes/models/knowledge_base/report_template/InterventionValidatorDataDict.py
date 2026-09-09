from typing import Literal, TypedDict

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

InterventionValidatorOperatorLiteral = Literal["exists", "missing", "condition"]
InterventionValidatorPrecedenceLiteral = Literal["required", "optional"]


class InterventionValidatorConditionClauseDataDict(TypedDict, total=False):
    classification: str
    comparator: FindingsValidatorComparatorLiteral
    value: ValidationScalar
    values: list[ValidationScalar]


class InterventionValidatorConditionDataDict(TypedDict, total=False):
    any: list[InterventionValidatorConditionClauseDataDict]
    all: list[InterventionValidatorConditionClauseDataDict]
    then_requires: list[ValidatorRequirementReferenceDataDict]


class InterventionValidatorQueryDataDict(TypedDict, total=False):
    finding: str
    intervention: str
    operator: InterventionValidatorOperatorLiteral
    params: ValidationParams
    condition: InterventionValidatorConditionDataDict


class InterventionValidatorHintDataDict(TypedDict, total=False):
    intervention_name: str
    precedence: InterventionValidatorPrecedenceLiteral
    intervention_types: list[str]


class InterventionValidatorDataDict(KnowledgebaseBaseModelDataDict):
    query: InterventionValidatorQueryDataDict
    finding: str
    intervention: str
    operator: InterventionValidatorOperatorLiteral
    precedence: InterventionValidatorPrecedenceLiteral
