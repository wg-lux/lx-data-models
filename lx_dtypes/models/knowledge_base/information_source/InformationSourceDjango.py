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
        return InformationSourceDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return INFORMATION_SOURCE_MODEL_LIST_TYPE_FIELDS
