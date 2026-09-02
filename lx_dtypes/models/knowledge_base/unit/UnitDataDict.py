from lx_dtypes.models.base.app_base_model.ddict.KnowledgebaseBaseModelDataDict import (
    KnowledgebaseBaseModelDataDict,
)


class UnitDataDict(KnowledgebaseBaseModelDataDict):
    abbreviation: str | None
    unit_types: str | list[str]
