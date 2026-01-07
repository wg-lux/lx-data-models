from typing import List

from lx_dtypes.models.base.app_base_model.ddict.KnowledgebaseBaseModelDataDict import (
    KnowledgebaseBaseModelDataDict,
)


class ClassificationChoiceDataDict(KnowledgebaseBaseModelDataDict):
    classification_choice_descriptors: List[str]
