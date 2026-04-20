from typing import List, Literal

from pydantic import BaseModel, Field

from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.knowledge_base.report_template.ReportFinding import (
    ReportTemplateFindingRequirement,
)
from lx_dtypes.models.knowledge_base.report_template.ReportTemplateSectionDataDict import (
    ReportTemplateSectionDataDict,
)


class ReportTemplateSectionField(BaseModel):
    key: str
    required: bool = False
    label: str | None = None
    source: Literal["patient", "patient_examination", "history"] | None = None


class ReportTemplateSection(KnowledgebaseBaseModel[ReportTemplateSectionDataDict]):
    position: int = 0
    types: List[str] = Field(default_factory=list)
    section_kind: Literal["findings", "patient_data", "history"] = "findings"
    fields: List[ReportTemplateSectionField] = Field(default_factory=list)
    findings: List[ReportTemplateFindingRequirement | str] = Field(default_factory=list)

    @classmethod
    def list_type_fields(cls) -> List[str]:
        return []

    @property
    def ddict_class(self) -> type[ReportTemplateSectionDataDict]:
        return ReportTemplateSectionDataDict
