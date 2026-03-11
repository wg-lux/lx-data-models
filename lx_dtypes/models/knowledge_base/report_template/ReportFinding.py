from typing import List

from pydantic import BaseModel, Field

from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.knowledge_base.report_template.ReportFindingDataDict import (
    ReportFindingDataDict,
)


class ReportTemplateClassificationRequirement(BaseModel):
    classification: str
    required: bool = False


class ReportTemplateFindingRequirement(BaseModel):
    finding: str
    required: bool = False
    multiple_allowed: bool = False
    classifications: List[ReportTemplateClassificationRequirement] = Field(
        default_factory=list
    )


class ReportFinding(KnowledgebaseBaseModel[ReportFindingDataDict]):
    finding: str
    required: bool = False
    multiple_allowed: bool = False
    classifications: List[ReportTemplateClassificationRequirement] = Field(
        default_factory=list
    )

    def as_requirement(self) -> ReportTemplateFindingRequirement:
        return ReportTemplateFindingRequirement(
            finding=self.finding,
            required=self.required,
            multiple_allowed=self.multiple_allowed,
            classifications=self.classifications,
        )

    @classmethod
    def list_type_fields(cls) -> List[str]:
        return []

    @property
    def ddict_class(self) -> type[ReportFindingDataDict]:
        return ReportFindingDataDict
