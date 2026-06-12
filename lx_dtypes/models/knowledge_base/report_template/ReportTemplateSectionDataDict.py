from typing import List, Literal, Optional

from lx_dtypes.models.base.app_base_model.ddict.KnowledgebaseBaseModelDataDict import (
    KnowledgebaseBaseModelDataDict,
)
from lx_dtypes.models.knowledge_base.report_template.ReportFindingDataDict import (
    ReportTemplateFindingRequirementDataDict,
)


class ReportTemplateSectionFieldDataDict(KnowledgebaseBaseModelDataDict):
    key: str
    required: bool
    label: str
    source: Literal["patient", "patient_examination", "history"]


class ReportTemplateSectionDataDict(KnowledgebaseBaseModelDataDict):
    position: int
    types: List[str]
    findings: List[ReportTemplateFindingRequirementDataDict | str]
    section_kind: Optional[Literal["findings", "patient_data", "history"]]
    fields: Optional[List[ReportTemplateSectionFieldDataDict]]
