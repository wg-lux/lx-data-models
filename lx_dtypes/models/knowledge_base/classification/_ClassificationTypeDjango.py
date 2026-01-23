from typing import TYPE_CHECKING

from django.db import models

from lx_dtypes.models.base.app_base_model.django.KnowledgebaseBaseModelDjango import (
    KnowledgebaseBaseModelDjango,
)
from lx_dtypes.names import CLASSIFICATION_TYPE_MODEL_LIST_TYPE_FIELDS

from .ClassificationTypeDataDict import (
    ClassificationTypeDataDict,
)


class ClassificationTypeDjango(
    KnowledgebaseBaseModelDjango[ClassificationTypeDataDict]
):
    if TYPE_CHECKING:
        from ._ClassificationDjango import ClassificationDjango

        classifications: models.QuerySet["ClassificationDjango"]

    @property
    def ddict_class(self) -> type[ClassificationTypeDataDict]:
        """
        The data-dictionary class associated with this model.

        Returns:
            type[ClassificationTypeDataDict]: The ClassificationTypeDataDict class used to represent this model's data.
        """
        return ClassificationTypeDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        """
        Provide the names of model fields that are treated as list-type for classification-type models.

        Returns:
            list[str]: Field names that should be handled as lists for this model.
        """
        return CLASSIFICATION_TYPE_MODEL_LIST_TYPE_FIELDS
