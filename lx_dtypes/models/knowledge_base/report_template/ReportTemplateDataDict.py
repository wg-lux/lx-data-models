import datetime
from typing import NotRequired, TypedDict

from lx_dtypes.models.base.app_base_model.ddict.KnowledgebaseBaseModelDataDict import (
    KnowledgebaseBaseModelDataDict,
)


class ReportTemplateValidatorsDataDict(TypedDict):
    examination_validators: list[str]
    findings_validators: list[str]
    classification_validators: list[str]
    intervention_validators: list[str]
    unit_validators: list[str]


class ReportTemplateGuidelineReferenceDataDict(TypedDict):
    guideline_id: str
    title: str
    issuing_organization: str
    version: str
    publication_date: datetime.date
    canonical_url: str
    cited_sections: list[str]


class ReportTemplateDataDict(KnowledgebaseBaseModelDataDict):
    examination: str
    version: NotRequired[str | None]
    guideline_references: NotRequired[list[ReportTemplateGuidelineReferenceDataDict]]
    coverage_version: NotRequired[str | None]
    coverage_concepts: NotRequired[list[object]]
    report_sections: list[str]
    validators: ReportTemplateValidatorsDataDict
