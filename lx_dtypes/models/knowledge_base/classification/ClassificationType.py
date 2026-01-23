from typing import List

from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.names import CLASSIFICATION_TYPE_MODEL_LIST_TYPE_FIELDS

from .ClassificationTypeDataDict import ClassificationTypeDataDict


class ClassificationType(KnowledgebaseBaseModel[ClassificationTypeDataDict]):
    @classmethod
    def list_type_fields(cls) -> List[str]:
        """
        Return the list of field names that identify classification types.

        Returns:
            List[str]: Field names used by the ClassificationType model to represent type identifiers.
        """
        return CLASSIFICATION_TYPE_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[ClassificationTypeDataDict]:
        """
        Return the data-dict class associated with this model.

        Returns:
            type[ClassificationTypeDataDict]: The ClassificationTypeDataDict class used as the model's data dictionary type.
        """
        return ClassificationTypeDataDict
