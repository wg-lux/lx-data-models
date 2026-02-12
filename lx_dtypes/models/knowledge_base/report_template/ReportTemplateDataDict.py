from typing import List

from lx_dtypes.models.base.app_base_model.ddict.KnowledgebaseBaseModelDataDict import (
    KnowledgebaseBaseModelDataDict,
)
from lx_dtypes.models.knowledge_base.report_template.common import (
    ReportTemplateValidatorsDataDict,
)


class ReportTemplateDataDict(KnowledgebaseBaseModelDataDict):
    examination: str
    report_sections: List[str]
    validators: ReportTemplateValidatorsDataDict
