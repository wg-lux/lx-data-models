from typing import Any, Dict

from lx_dtypes.models.base.app_base_model.ddict.KnowledgebaseBaseModelDataDict import (
    KnowledgebaseBaseModelDataDict,
)


class FindingsValidatorDataDict(KnowledgebaseBaseModelDataDict):
    query: Dict[str, Any]
    finding: str
    operator: str
