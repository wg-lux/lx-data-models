from typing import TYPE_CHECKING

from django.db import models

from lx_dtypes.models.base.app_base_model.django.KnowledgebaseBaseModelDjango import (
    KnowledgebaseBaseModelDjango,
)
from lx_dtypes.models.knowledge_base.intervention.InterventionTypeDataDict import (
    InterventionTypeDataDict,
)
from lx_dtypes.names import INTERVENTION_TYPE_MODEL_LIST_TYPE_FIELDS


class InterventionTypeDjango(KnowledgebaseBaseModelDjango[InterventionTypeDataDict]):
    if TYPE_CHECKING:
        from .InterventionDjango import (
            InterventionDjango,
        )

        interventions: models.QuerySet["InterventionDjango"]
        # patient_finding_interventions #TODO

    @property
    def ddict_class(self) -> type[InterventionTypeDataDict]:
        """
        Return the data-dictionary class associated with this model.

        Returns:
            type[InterventionTypeDataDict]: The InterventionTypeDataDict class used to represent this model's structured data.
        """
        return InterventionTypeDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        """
        Provide the list-type field names used by the InterventionType model.

        Returns:
            list[str]: Field names in the model that should be treated as lists.
        """
        return INTERVENTION_TYPE_MODEL_LIST_TYPE_FIELDS
