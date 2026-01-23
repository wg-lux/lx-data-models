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
        """
        Provide the data-dictionary class used by this model.

        Returns:
            type[UnitTypeDataDict]: The UnitTypeDataDict class used for this model's data dictionary.
        """
        return UnitTypeDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        """
        List model field names that are treated as list types for UnitType models.

        Returns:
            list_type_fields (list[str]): Ordered list of field names that should be interpreted as lists.
        """
        return UNIT_TYPE_MODEL_LIST_TYPE_FIELDS
