from lx_dtypes.models.base.app_base_model.ddict.KnowledgebaseBaseModelDataDict import (
    KnowledgebaseBaseModelDataDict,
)


class UnitDataDict(KnowledgebaseBaseModelDataDict):
    abbreviation: str
    unit_types: str
