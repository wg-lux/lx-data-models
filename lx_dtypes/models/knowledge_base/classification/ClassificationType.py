from typing import List

from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.names import CLASSIFICATION_TYPE_MODEL_LIST_TYPE_FIELDS

from .ClassificationTypeDataDict import ClassificationTypeDataDict


class ClassificationType(KnowledgebaseBaseModel[ClassificationTypeDataDict]):
    @classmethod
    def list_type_fields(cls) -> List[str]:
        return CLASSIFICATION_TYPE_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[ClassificationTypeDataDict]:
        return ClassificationTypeDataDict
