from typing import Literal

from lx_dtypes.models.base.app_base_model.ddict.KnowledgebaseBaseModelDataDict import (
    KnowledgebaseBaseModelDataDict,
)
from lx_dtypes.models.knowledge_base.report_template.ReportFindingDataDict import (
    ReportTemplateFindingRequirementDataDict,
)


class ReportTemplateSectionFieldDataDict(KnowledgebaseBaseModelDataDict):
    """Serialized :class:`ReportTemplateSectionField`."""

    key: str
    required: bool
    label: str
    source: Literal["patient", "patient_examination", "history"]


class ReportTemplateSectionDataDict(KnowledgebaseBaseModelDataDict):
    """Serialized :class:`ReportTemplateSection` knowledge-base record."""

    title_de: str
    title_en: str
    position: int
    types: list[str]
    findings: list[ReportTemplateFindingRequirementDataDict | str]
    section_kind: Literal["findings", "patient_data", "history", "medications"] | None
    fields: list[ReportTemplateSectionFieldDataDict] | None
