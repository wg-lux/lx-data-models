from typing import List

from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.knowledge_base.finding.FindingTypeDataDict import (
    FindingTypeDataDict,
)
from lx_dtypes.names import FINDING_TYPE_MODEL_LIST_TYPE_FIELDS


class FindingType(KnowledgebaseBaseModel[FindingTypeDataDict]):
    @classmethod
    def list_type_fields(cls) -> List[str]:
        return FINDING_TYPE_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[FindingTypeDataDict]:
        return FindingTypeDataDict
