from typing import List, Literal, Self

from pydantic import BaseModel, Field, model_validator

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
    title_de: str = ""
    title_en: str = ""
    position: int = 0
    types: List[str] = Field(default_factory=list)
    section_kind: Literal["findings", "patient_data", "history"] = "findings"
    fields: List[ReportTemplateSectionField] = Field(default_factory=list)
    findings: List[ReportTemplateFindingRequirement | str] = Field(default_factory=list)

    @model_validator(mode="after")
    def guarantee_localized_titles(self) -> Self:
        """Always expose localized titles; legacy sections fall back upstream."""

        if not self.title_de:
            self.title_de = (
                self.name_de
                if self.name_de and self.name_de != "unknown"
                else self.name
            )
        if not self.title_en:
            self.title_en = (
                self.name_en
                if self.name_en and self.name_en != "unknown"
                else self.name
            )
        return self

    @classmethod
    def list_type_fields(cls) -> List[str]:
        return []

    @property
    def ddict_class(self) -> type[ReportTemplateSectionDataDict]:
        return ReportTemplateSectionDataDict
