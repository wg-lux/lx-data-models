from typing import List

from lx_dtypes.models.base.app_base_model.ddict.KnowledgebaseBaseModelDataDict import (
    KnowledgebaseBaseModelDataDict,
)


class FindingDataDict(KnowledgebaseBaseModelDataDict):
    classifications: List[str]
    interventions: List[str]
    finding_types: List[str]
