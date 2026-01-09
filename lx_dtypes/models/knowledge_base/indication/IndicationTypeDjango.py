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
        return IndicationTypeDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return INDICATION_TYPE_MODEL_LIST_TYPE_FIELDS
