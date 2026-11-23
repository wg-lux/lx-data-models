import datetime
from typing import NotRequired, TypedDict

from lx_dtypes.models.base.app_base_model.ddict.KnowledgebaseBaseModelDataDict import (
    KnowledgebaseBaseModelDataDict,
)
from lx_dtypes.models.contracts.reporting_types import ReportVerbosity


class ReportTemplateValidatorsDataDict(TypedDict):
    """Serialized :class:`ReportTemplateValidators`."""

    examination_validators: list[str]
    findings_validators: list[str]
    classification_validators: list[str]
    intervention_validators: list[str]
    unit_validators: list[str]


class ReportTemplateGuidelineReferenceDataDict(TypedDict):
    """Serialized :class:`ReportTemplateGuidelineReference`."""

    guideline_id: str
    title: str
    issuing_organization: str
    version: str
    publication_date: datetime.date
    canonical_url: str
    cited_sections: list[str]


class ReportTemplateDataDict(KnowledgebaseBaseModelDataDict):
    """Serialized :class:`ReportTemplate` knowledge-base record."""

    examination: str
    verbosity_options: NotRequired[list[ReportVerbosity]]
    version: NotRequired[str | None]
    guideline_references: NotRequired[list[ReportTemplateGuidelineReferenceDataDict]]
    coverage_version: NotRequired[str | None]
    coverage_concepts: NotRequired[list[object]]
    report_sections: list[str]
    validators: ReportTemplateValidatorsDataDict
