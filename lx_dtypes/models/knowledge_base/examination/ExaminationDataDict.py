from typing import List

from lx_dtypes.models.base.app_base_model.ddict.KnowledgebaseBaseModelDataDict import (
    KnowledgebaseBaseModelDataDict,
)


class ExaminationDataDict(KnowledgebaseBaseModelDataDict):
    findings: List[str]
    examination_types: List[str]
    indications: List[str]
