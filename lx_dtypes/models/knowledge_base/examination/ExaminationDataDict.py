from lx_dtypes.models.base.app_base_model.ddict.KnowledgebaseBaseModelDataDict import (
    KnowledgebaseBaseModelDataDict,
)


class ExaminationDataDict(KnowledgebaseBaseModelDataDict):
    findings: list[str]
    examination_types: list[str]
    indications: list[str]
