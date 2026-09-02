from lx_dtypes.models.base.app_base_model.ddict.KnowledgebaseBaseModelDataDict import (
    KnowledgebaseBaseModelDataDict,
)


class ClassificationDataDict(KnowledgebaseBaseModelDataDict):
    classification_choices: list[str]
    classification_types: list[str]
