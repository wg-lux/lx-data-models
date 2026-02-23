from typing import List, Literal, NotRequired

from lx_dtypes.models.base.app_base_model.ddict.KnowledgebaseBaseModelDataDict import (
    KnowledgebaseBaseModelDataDict,
)
from lx_dtypes.models.knowledge_base.report_template.common import (
    ReportTemplateFindingRequirementDataDict,
    ReportTemplateSectionFieldDataDict,
)


class ReportTemplateSectionDataDict(KnowledgebaseBaseModelDataDict):
    position: int
    types: List[str]
    findings: List[ReportTemplateFindingRequirementDataDict | str]
    section_kind: NotRequired[Literal["findings", "patient_data", "history"]]
    fields: NotRequired[List[ReportTemplateSectionFieldDataDict]]
