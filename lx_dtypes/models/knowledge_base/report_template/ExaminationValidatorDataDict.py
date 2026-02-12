from typing import List

from lx_dtypes.models.base.app_base_model.ddict.KnowledgebaseBaseModelDataDict import (
    KnowledgebaseBaseModelDataDict,
)


class ExaminationValidatorDataDict(KnowledgebaseBaseModelDataDict):
    finding_validators: List[str]
    examination_validators: List[str]
