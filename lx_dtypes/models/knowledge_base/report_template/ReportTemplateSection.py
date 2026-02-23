from typing import List, Literal

from pydantic import Field

from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.knowledge_base.report_template.ReportTemplateSectionDataDict import (
    ReportTemplateSectionDataDict,
)
from lx_dtypes.models.knowledge_base.report_template.common import (
    ReportTemplateFindingRequirementInput,
    ReportTemplateSectionField,
)


class ReportTemplateSection(KnowledgebaseBaseModel[ReportTemplateSectionDataDict]):
    position: int = 0
    types: List[str] = Field(default_factory=list)
    section_kind: Literal["findings", "patient_data", "history"] = "findings"
    fields: List[ReportTemplateSectionField] = Field(default_factory=list)
    findings: List[ReportTemplateFindingRequirementInput] = Field(default_factory=list)

    @classmethod
    def list_type_fields(cls) -> List[str]:
        return []

    @property
    def ddict_class(self) -> type[ReportTemplateSectionDataDict]:
        return ReportTemplateSectionDataDict
