from typing import TYPE_CHECKING

from django.db import models

from lx_dtypes.models.base.app_base_model.django.KnowledgebaseBaseModelDjango import (
    KnowledgebaseBaseModelDjango,
)
from lx_dtypes.names import CLASSIFICATION_MODEL_LIST_TYPE_FIELDS, FieldNames

from .ClassificationDataDict import (
    ClassificationDataDict,
)

if TYPE_CHECKING:
    from lx_dtypes.models.knowledge_base.classification_choice.ClassificationChoiceDjango import (
        ClassificationChoiceDjango,
    )

    from ._ClassificationTypeDjango import ClassificationTypeDjango


class ClassificationDjango(KnowledgebaseBaseModelDjango[ClassificationDataDict]):
    classification_types: models.ManyToManyField[
        "ClassificationTypeDjango", "ClassificationTypeDjango"
    ] = models.ManyToManyField(
        "ClassificationTypeDjango", related_name=FieldNames.CLASSIFICATIONS.value
    )
    classification_choices: models.ManyToManyField[
        "ClassificationChoiceDjango", "ClassificationChoiceDjango"
    ] = models.ManyToManyField(
        "ClassificationChoiceDjango",
        related_name=FieldNames.CLASSIFICATIONS.value,
    )

    @property
    def ddict_class(self) -> type[ClassificationDataDict]:
        """
        Provide the data-dictionary class associated with this model.

        Returns:
            The `ClassificationDataDict` class.
        """
        return ClassificationDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        """
        List model field names that are treated as list-type fields.

        Returns:
            list[str]: Field name strings that should be treated as list-type fields.
        """
        return CLASSIFICATION_MODEL_LIST_TYPE_FIELDS
