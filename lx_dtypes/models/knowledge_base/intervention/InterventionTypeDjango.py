from typing import TYPE_CHECKING

from django.db import models

from lx_dtypes.models.base.app_base_model.django.KnowledgebaseBaseModelDjango import (
    KnowledgebaseBaseModelDjango,
)
from lx_dtypes.models.knowledge_base.intervention.InterventionDjango import (
    InterventionDjango,
)
from lx_dtypes.models.knowledge_base.intervention.InterventionTypeDataDict import (
    InterventionTypeDataDict,
)
from lx_dtypes.names import INTERVENTION_TYPE_MODEL_LIST_TYPE_FIELDS


class InterventionTypeDjango(KnowledgebaseBaseModelDjango[InterventionTypeDataDict]):
    if TYPE_CHECKING:
        interventions: models.QuerySet["InterventionDjango"]
        # patient_finding_interventions #TODO

    @property
    def ddict_class(self) -> type[InterventionTypeDataDict]:
        return InterventionTypeDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return INTERVENTION_TYPE_MODEL_LIST_TYPE_FIELDS
