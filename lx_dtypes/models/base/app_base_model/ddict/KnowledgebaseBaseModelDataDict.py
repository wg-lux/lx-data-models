from lx_dtypes.models.base.app_base_model.ddict.AppBaseModelNamesUUIDTagsDataDict import (
    AppBaseModelNamesUUIDTagsDataDict,
)


class KnowledgebaseBaseModelDataDict(AppBaseModelNamesUUIDTagsDataDict):
    """
    Data dictionary for knowledgebase base models. Inherits from AppBaseModelNamesUUIDTagsDataDict.
    Fields:
    - kb_module_name: str
    """

    kb_module_name: str
