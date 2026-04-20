from typing import List, TypedDict

from lx_dtypes.models.base.app_base_model.ddict.KnowledgebaseBaseModelDataDict import (
    KnowledgebaseBaseModelDataDict,
)


class ReportTemplateValidatorsDataDict(TypedDict):
    examination_validators: List[str]
    findings_validators: List[str]
    classification_validators: List[str]
    intervention_validators: List[str]
    unit_validators: List[str]


class ReportTemplateDataDict(KnowledgebaseBaseModelDataDict):
    examination: str
    report_sections: List[str]
    validators: ReportTemplateValidatorsDataDict
