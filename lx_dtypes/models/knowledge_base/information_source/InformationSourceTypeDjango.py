from typing import TYPE_CHECKING

from django.db import models

from lx_dtypes.models.base.app_base_model.django.KnowledgebaseBaseModelDjango import (
    KnowledgebaseBaseModelDjango,
)
from lx_dtypes.names import INFORMATION_SOURCE_TYPE_MODEL_LIST_TYPE_FIELDS

from .InformationSourceTypeDataDict import (
    InformationSourceTypeDataDict,
)

if TYPE_CHECKING:
    from lx_dtypes.models.knowledge_base.information_source.InformationSourceDjango import (
        InformationSourceDjango,
    )


class InformationSourceTypeDjango(
    KnowledgebaseBaseModelDjango["InformationSourceTypeDataDict"]
):
    if TYPE_CHECKING:
        information_sources: models.QuerySet["InformationSourceDjango"]

    @property
    def ddict_class(self) -> type["InformationSourceTypeDataDict"]:
        """
        Provide the data-dictionary class associated with this model.

        Returns:
            type[InformationSourceTypeDataDict]: The InformationSourceTypeDataDict class used to represent this model's data dictionary.
        """
        return InformationSourceTypeDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        """
        Provide the model field names that represent list-type attributes.

        Returns:
            list[str]: Field names that should be treated as list-type fields for this model.
        """
        return INFORMATION_SOURCE_TYPE_MODEL_LIST_TYPE_FIELDS
