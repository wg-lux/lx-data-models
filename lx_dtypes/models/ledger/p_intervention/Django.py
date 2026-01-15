from typing import TYPE_CHECKING

from django.db import models

from lx_dtypes.models.base.app_base_model.django.LedgerBaseModelDjango import (
    LedgerBaseModelDjango,
)
from lx_dtypes.names import (
    P_INTERVENTION_MODEL_LIST_TYPE_FIELDS,
    P_INTERVENTION_MODEL_NESTED_FIELDS,
    FieldNames,
)

if TYPE_CHECKING:
    from lx_dtypes.models.knowledge_base.intervention.InterventionDjango import (
        InterventionDjango,
    )
    from lx_dtypes.models.ledger.p_interventions.Django import (
        PFindingInterventionsDjango,
    )

from .DataDict import (
    PFindingInterventionDataDict,
)


class PFindingInterventionDjango(LedgerBaseModelDjango[PFindingInterventionDataDict]):
    patient_finding_interventions: models.ForeignKey[
        "PFindingInterventionsDjango", "PFindingInterventionsDjango"
    ] = models.ForeignKey(
        "PFindingInterventionsDjango",
        related_name=FieldNames.PATIENT_FINDING_INTERVENTIONS.value,
        on_delete=models.CASCADE,
    )
    intervention: models.ForeignKey["InterventionDjango", "InterventionDjango"] = (
        models.ForeignKey(
            "InterventionDjango",
            related_name=FieldNames.PATIENT_FINDING_INTERVENTIONS.value,
            on_delete=models.CASCADE,
        )
    )

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return P_INTERVENTION_MODEL_LIST_TYPE_FIELDS

    @classmethod
    def nested_fields(cls) -> list[str]:
        return P_INTERVENTION_MODEL_NESTED_FIELDS

    @property
    def ddict_class(self) -> type[PFindingInterventionDataDict]:
        return PFindingInterventionDataDict

    class Meta(LedgerBaseModelDjango.Meta):
        abstract = False
