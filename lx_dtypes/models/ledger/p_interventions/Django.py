from typing import TYPE_CHECKING

from django.db import models

from lx_dtypes.models.base.app_base_model.django.LedgerBaseModelDjango import (
    LedgerBaseModelDjango,
)
from lx_dtypes.names import (
    P_INTERVENTIONS_MODEL_LIST_TYPE_FIELDS,
    P_INTERVENTIONS_MODEL_NESTED_FIELDS,
)

from .DataDict import (
    PFindingInterventionsDataDict,
)

if TYPE_CHECKING:
    from lx_dtypes.models.ledger.p_finding.Django import (
        PFindingDjango,
    )
    from lx_dtypes.models.ledger.p_intervention.Django import (
        PFindingInterventionDjango,
    )


class PFindingInterventionsDjango(LedgerBaseModelDjango[PFindingInterventionsDataDict]):
    patient_finding: models.ForeignKey["PFindingDjango", "PFindingDjango"] = (
        models.ForeignKey(
            "PFindingDjango",
            related_name="patient_finding_interventions",
            on_delete=models.CASCADE,
        )
    )

    if TYPE_CHECKING:
        patient_finding_interventions: models.Manager["PFindingInterventionDjango"]

    @property
    def ddict_class(self) -> type[PFindingInterventionsDataDict]:
        return PFindingInterventionsDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return P_INTERVENTIONS_MODEL_LIST_TYPE_FIELDS

    @classmethod
    def nested_fields(cls) -> list[str]:
        return P_INTERVENTIONS_MODEL_NESTED_FIELDS
