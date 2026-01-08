from typing import List

from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.knowledge_base.information_source.InformationSourceTypeDataDict import (
    InformationSourceTypeDataDict,
)
from lx_dtypes.names import INFORMATION_SOURCE_TYPE_MODEL_LIST_TYPE_FIELDS


class InformationSourceType(KnowledgebaseBaseModel[InformationSourceTypeDataDict]):
    @classmethod
    def list_type_fields(cls) -> List[str]:
        return INFORMATION_SOURCE_TYPE_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[InformationSourceTypeDataDict]:
        return InformationSourceTypeDataDict
