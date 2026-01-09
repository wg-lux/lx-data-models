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
        "InterventionTypeDjango", related_name=FieldNames.INTERVENTION_TYPES.value
    )

    @property
    def ddict_class(self) -> type[InterventionDataDict]:
        return InterventionDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return INTERVENTION_MODEL_LIST_TYPE_FIELDS
