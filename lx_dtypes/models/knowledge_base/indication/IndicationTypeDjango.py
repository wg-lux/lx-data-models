from typing import TYPE_CHECKING

from django.db import models

from lx_dtypes.models.base.app_base_model.django.KnowledgebaseBaseModelDjango import (
    KnowledgebaseBaseModelDjango,
)
from lx_dtypes.names import INDICATION_TYPE_MODEL_LIST_TYPE_FIELDS

from .IndicationTypeDataDict import IndicationTypeDataDict


class IndicationTypeDjango(KnowledgebaseBaseModelDjango[IndicationTypeDataDict]):
    if TYPE_CHECKING:
        from .IndicationDjango import (
            IndicationDjango,
        )

        indications: models.QuerySet["IndicationDjango"]
        # patient_finding_indications #TODO

    @property
    def ddict_class(self) -> type[IndicationTypeDataDict]:
        """
        Return the data-dict class associated with this model.

        Returns:
            data_dict_class (type[IndicationTypeDataDict]): The IndicationTypeDataDict class used to represent this model's structured data.
        """
        return IndicationTypeDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        """
        Return the model field names that should be treated as list-type for indication-type models.

        Returns:
            list[str]: Field name strings that must be serialized/deserialized as lists for IndicationType models.
        """
        return INDICATION_TYPE_MODEL_LIST_TYPE_FIELDS
