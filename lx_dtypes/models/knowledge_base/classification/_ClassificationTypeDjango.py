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
        return ClassificationTypeDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return CLASSIFICATION_TYPE_MODEL_LIST_TYPE_FIELDS
