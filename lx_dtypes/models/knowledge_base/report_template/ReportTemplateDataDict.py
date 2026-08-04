import datetime
from typing import List, NotRequired, TypedDict

from lx_dtypes.models.base.app_base_model.ddict.KnowledgebaseBaseModelDataDict import (
    KnowledgebaseBaseModelDataDict,
)


class ReportTemplateValidatorsDataDict(TypedDict):
    examination_validators: List[str]
    findings_validators: List[str]
    classification_validators: List[str]
    intervention_validators: List[str]
    unit_validators: List[str]


class ReportTemplateGuidelineReferenceDataDict(TypedDict):
    guideline_id: str
    title: str
    issuing_organization: str
    version: str
    publication_date: datetime.date
    canonical_url: str
    cited_sections: List[str]


class ReportTemplateDataDict(KnowledgebaseBaseModelDataDict):
    examination: str
    version: NotRequired[str | None]
    guideline_references: NotRequired[List[ReportTemplateGuidelineReferenceDataDict]]
    coverage_version: NotRequired[str | None]
    coverage_concepts: NotRequired[List[object]]
    report_sections: List[str]
    validators: ReportTemplateValidatorsDataDict
