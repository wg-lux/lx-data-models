from typing import List

from lx_dtypes.models.base.app_base_model.ddict.KnowledgebaseBaseModelDataDict import (
    KnowledgebaseBaseModelDataDict,
)
from lx_dtypes.models.knowledge_base.report_template.common import (
    ReportTemplateFindingRequirementDataDict,
)


class ReportTemplateSectionDataDict(KnowledgebaseBaseModelDataDict):
    position: int
    types: List[str]
    findings: List[ReportTemplateFindingRequirementDataDict | str]
