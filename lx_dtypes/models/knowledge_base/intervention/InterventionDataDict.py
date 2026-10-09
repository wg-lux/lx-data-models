from lx_dtypes.models.base.app_base_model.ddict.KnowledgebaseBaseModelDataDict import (
    KnowledgebaseBaseModelDataDict,
)


class InterventionDataDict(KnowledgebaseBaseModelDataDict):
    intervention_types: list[str]
