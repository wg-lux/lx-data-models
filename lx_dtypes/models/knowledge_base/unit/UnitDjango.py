from typing import TYPE_CHECKING

from django.db import models

from lx_dtypes.models.base.app_base_model.django.KnowledgebaseBaseModelDjango import (
    KnowledgebaseBaseModelDjango,
)
from lx_dtypes.models.knowledge_base.unit.UnitDataDict import (
    UnitDataDict,
)
from lx_dtypes.names import UNIT_MODEL_LIST_TYPE_FIELDS, FieldNames

if TYPE_CHECKING:
    from lx_dtypes.models.knowledge_base.unit.UnitTypeDjango import (
        UnitTypeDjango,
    )

from lx_dtypes.utils.django_field_types import CharFieldType


class UnitDjango(KnowledgebaseBaseModelDjango[UnitDataDict]):
    unit_types: models.ManyToManyField["UnitTypeDjango", "UnitTypeDjango"] = (
        models.ManyToManyField("UnitTypeDjango", related_name=FieldNames.UNITS.value)
    )
    abbreviation: CharFieldType = models.CharField(max_length=50)

    if TYPE_CHECKING:
        from lx_dtypes.models.knowledge_base.classification_choice_descriptor.ClassificationChoiceDescriptorDjango import (
            ClassificationChoiceDescriptorDjango,
        )

        classification_choice_descriptors: models.QuerySet[
            "ClassificationChoiceDescriptorDjango"
        ]

    @property
    def ddict_class(self) -> type[UnitDataDict]:
        """
        Provide the data-dictionary class used by this model.

        Returns:
            type[UnitDataDict]: The UnitDataDict class representing this model's data dictionary.
        """
        return UnitDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        """
        Provide the names of this model's fields that represent list/collection types.

        Returns:
            list[str]: Field name strings that should be treated as list-type fields.
        """
        return UNIT_MODEL_LIST_TYPE_FIELDS
