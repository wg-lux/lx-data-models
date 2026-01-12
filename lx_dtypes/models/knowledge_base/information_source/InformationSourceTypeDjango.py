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
        return InformationSourceTypeDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return INFORMATION_SOURCE_TYPE_MODEL_LIST_TYPE_FIELDS
