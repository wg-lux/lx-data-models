from typing import TYPE_CHECKING

from django.db import models

from lx_dtypes.models.base.app_base_model.django.KnowledgebaseBaseModelDjango import (
    KnowledgebaseBaseModelDjango,
)
from lx_dtypes.names import CLASSIFICATION_CHOICE_MODEL_LIST_TYPE_FIELDS, FieldNames

from .ClassificationChoiceDataDict import (
    ClassificationChoiceDataDict,
)

if TYPE_CHECKING:
    from lx_dtypes.models.knowledge_base.classification_choice_descriptor.ClassificationChoiceDescriptorDjango import (
        ClassificationChoiceDescriptorDjango,
    )


class ClassificationChoiceDjango(
    KnowledgebaseBaseModelDjango[ClassificationChoiceDataDict]
):
    classification_choice_descriptors: models.ManyToManyField[
        "ClassificationChoiceDescriptorDjango", "ClassificationChoiceDescriptorDjango"
    ] = models.ManyToManyField(
        "ClassificationChoiceDescriptorDjango",
        related_name=FieldNames.CLASSIFICATION_CHOICES.value,
        blank=True,
    )

    @property
    def ddict_class(self) -> type[ClassificationChoiceDataDict]:
        """
        Provide the data-dictionary class associated with this model.

        Returns:
            type[ClassificationChoiceDataDict]: The `ClassificationChoiceDataDict` class used to represent this model's data dictionary.
        """
        return ClassificationChoiceDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        """
        Get the configured list-type field names for ClassificationChoice models.

        Returns:
            list[str]: Field names that are treated as list-type for this model.
        """
        return CLASSIFICATION_CHOICE_MODEL_LIST_TYPE_FIELDS
