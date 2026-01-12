from typing import TYPE_CHECKING

from django.db import models

from lx_dtypes.models.base.app_base_model.django.KnowledgebaseBaseModelDjango import (
    KnowledgebaseBaseModelDjango,
)
from lx_dtypes.models.knowledge_base.unit.UnitTypeDataDict import (
    UnitTypeDataDict,
)
from lx_dtypes.names import UNIT_TYPE_MODEL_LIST_TYPE_FIELDS


class UnitTypeDjango(KnowledgebaseBaseModelDjango[UnitTypeDataDict]):
    if TYPE_CHECKING:
        from .UnitDjango import UnitDjango

        units: models.QuerySet["UnitDjango"]

    @property
    def ddict_class(self) -> type[UnitTypeDataDict]:
        return UnitTypeDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return UNIT_TYPE_MODEL_LIST_TYPE_FIELDS
