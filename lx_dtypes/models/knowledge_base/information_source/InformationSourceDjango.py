from typing import TYPE_CHECKING

from django.db import models

from lx_dtypes.models.base.app_base_model.django.KnowledgebaseBaseModelDjango import (
    KnowledgebaseBaseModelDjango,
)
from lx_dtypes.names import INFORMATION_SOURCE_MODEL_LIST_TYPE_FIELDS, FieldNames

from .InformationSourceDataDict import (
    InformationSourceDataDict,
)

if TYPE_CHECKING:
    from lx_dtypes.models.knowledge_base.information_source.InformationSourceTypeDjango import (
        InformationSourceTypeDjango,
    )


class InformationSourceDjango(
    KnowledgebaseBaseModelDjango["InformationSourceDataDict"]
):
    information_source_types: models.ManyToManyField[
        "InformationSourceTypeDjango",
        "InformationSourceTypeDjango",
    ] = models.ManyToManyField(
        "InformationSourceTypeDjango",
        related_name=FieldNames.INFORMATION_SOURCES.value,
    )

    @property
    def ddict_class(self) -> type["InformationSourceDataDict"]:
        """
        Expose the data-dictionary class associated with this model.

        Returns:
            InformationSourceDataDict: The class used as the model's data dictionary.
        """
        return InformationSourceDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        """
        Provide the names of model fields that should be treated as list (array) types.

        Returns:
            list[str]: Field names that are configured as list-type fields for this model.
        """
        return INFORMATION_SOURCE_MODEL_LIST_TYPE_FIELDS
