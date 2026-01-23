from typing import List

from lx_dtypes.models.base.app_base_model.ddict.KnowledgebaseBaseModelDataDict import (
    KnowledgebaseBaseModelDataDict,
)


class ClassificationDataDict(KnowledgebaseBaseModelDataDict):
    classification_choices: List[str]
    classification_types: List[str]
