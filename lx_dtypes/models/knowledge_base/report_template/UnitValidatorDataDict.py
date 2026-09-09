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

UnitValidatorOperatorLiteral = Literal["exists", "missing", "condition"]
UnitValidatorPrecedenceLiteral = Literal["required", "optional"]


class UnitValidatorConditionClauseDataDict(TypedDict, total=False):
    classification: str
    comparator: FindingsValidatorComparatorLiteral
    value: ValidationScalar
    values: list[ValidationScalar]


class UnitValidatorConditionDataDict(TypedDict, total=False):
    any: list[UnitValidatorConditionClauseDataDict]
    all: list[UnitValidatorConditionClauseDataDict]
    then_requires: list[ValidatorRequirementReferenceDataDict]


class UnitValidatorQueryDataDict(TypedDict, total=False):
    finding: str
    classification: str
    unit: str
    operator: UnitValidatorOperatorLiteral
    params: ValidationParams
    condition: UnitValidatorConditionDataDict


class UnitValidatorHintDataDict(TypedDict, total=False):
    unit_name: str
    precedence: UnitValidatorPrecedenceLiteral
    abbreviation: str
    unit_types: list[str]


class UnitValidatorDataDict(KnowledgebaseBaseModelDataDict):
    query: UnitValidatorQueryDataDict
    finding: str
    classification: str
    unit: str
    operator: UnitValidatorOperatorLiteral
    precedence: UnitValidatorPrecedenceLiteral
