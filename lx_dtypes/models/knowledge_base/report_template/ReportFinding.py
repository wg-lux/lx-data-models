from typing import List

from pydantic import Field

from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.knowledge_base.report_template.ReportFindingDataDict import (
    ReportFindingDataDict,
)
from lx_dtypes.models.knowledge_base.report_template.common import (
    ReportTemplateClassificationRequirement,
    ReportTemplateFindingRequirement,
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
