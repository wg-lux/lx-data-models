from typing import TYPE_CHECKING

from django.db import models

from lx_dtypes.models.base.app_base_model.django.KnowledgebaseBaseModelDjango import (
    KnowledgebaseBaseModelDjango,
)
from lx_dtypes.models.knowledge_base.intervention.InterventionDataDict import (
    InterventionDataDict,
)
from lx_dtypes.names import INTERVENTION_MODEL_LIST_TYPE_FIELDS, FieldNames

if TYPE_CHECKING:
    from lx_dtypes.models.knowledge_base.intervention.InterventionTypeDjango import (
        InterventionTypeDjango,
    )


class InterventionDjango(KnowledgebaseBaseModelDjango[InterventionDataDict]):
    intervention_types: models.ManyToManyField[
        "InterventionTypeDjango", "InterventionTypeDjango"
    ] = models.ManyToManyField(
        "InterventionTypeDjango", related_name=FieldNames.INTERVENTIONS.value
    )

    if TYPE_CHECKING:
        from lx_dtypes.models.knowledge_base.indication.IndicationDjango import (
            IndicationDjango,
        )

        indications: models.QuerySet["IndicationDjango"]

    @property
    def ddict_class(self) -> type[InterventionDataDict]:
        """
        Provide the data-dictionary class associated with this model.

        Returns:
            The `InterventionDataDict` class used to represent this model's data as a dictionary.
        """
        return InterventionDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        """
        Return the names of model fields that represent list-typed relationships for the Intervention model.

        Returns:
            list[str]: Field name strings that should be treated as list-typed (e.g., many-to-many or related lists).
        """
        return INTERVENTION_MODEL_LIST_TYPE_FIELDS
