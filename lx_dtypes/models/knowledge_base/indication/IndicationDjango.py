from typing import TYPE_CHECKING

from django.db import models

from lx_dtypes.models.base.app_base_model.django.KnowledgebaseBaseModelDjango import (
    KnowledgebaseBaseModelDjango,
)
from lx_dtypes.models.knowledge_base.indication.IndicationDataDict import (
    IndicationDataDict,
)
from lx_dtypes.names import INDICATION_MODEL_LIST_TYPE_FIELDS, FieldNames

if TYPE_CHECKING:
    from lx_dtypes.models.knowledge_base.intervention.InterventionDjango import (
        InterventionDjango,
    )

    from .IndicationTypeDjango import (
        IndicationTypeDjango,
    )


class IndicationDjango(KnowledgebaseBaseModelDjango[IndicationDataDict]):
    indication_types: models.ManyToManyField[
        "IndicationTypeDjango", "IndicationTypeDjango"
    ] = models.ManyToManyField(
        "IndicationTypeDjango", related_name=FieldNames.INDICATIONS.value
    )
    interventions: models.ManyToManyField[
        "InterventionDjango", "InterventionDjango"
    ] = models.ManyToManyField(
        "InterventionDjango", related_name=FieldNames.INDICATIONS.value
    )

    @property
    def ddict_class(self) -> type[IndicationDataDict]:
        """
        Return the data-dictionary class associated with this model.

        Returns:
            ddict_class (type[IndicationDataDict]): The IndicationDataDict class used to represent this model's structured data.
        """
        return IndicationDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        """
        List field names that should be treated as list types for the Indication model.

        Returns:
            list[str]: Field name strings that represent list-typed fields on the model.
        """
        return INDICATION_MODEL_LIST_TYPE_FIELDS
