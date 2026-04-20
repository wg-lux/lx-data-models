from typing import List, Union

from lx_dtypes.models.base.app_base_model.ddict.KnowledgebaseBaseModelDataDict import (
    KnowledgebaseBaseModelDataDict,
)


class UnitDataDict(KnowledgebaseBaseModelDataDict):
    abbreviation: str | None
    unit_types: Union[str, List[str]]
