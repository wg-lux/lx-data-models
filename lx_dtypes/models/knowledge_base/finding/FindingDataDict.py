from lx_dtypes.models.base.app_base_model.ddict.KnowledgebaseBaseModelDataDict import (
    KnowledgebaseBaseModelDataDict,
)


class FindingDataDict(KnowledgebaseBaseModelDataDict):
    classifications: list[str]
    interventions: list[str]
    caused_by_interventions: list[str]
    finding_types: list[str]
