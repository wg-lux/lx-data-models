from typing import List

from lx_dtypes.models.base.app_base_model.ddict.KnowledgebaseBaseModelDataDict import (
    KnowledgebaseBaseModelDataDict,
)


class InformationSourceDataDict(KnowledgebaseBaseModelDataDict):
    information_source_types: List[str]
