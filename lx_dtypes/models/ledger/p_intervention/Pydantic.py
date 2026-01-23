from typing import List

from lx_dtypes.models.base.app_base_model.pydantic.LedgerBaseModel import (
    LedgerBaseModel,
)
from lx_dtypes.names import (
    P_INTERVENTIONS_MODEL_LIST_TYPE_FIELDS,
    P_INTERVENTIONS_MODEL_NESTED_FIELDS,
)

from .DataDict import (
    PFindingInterventionDataDict,
)


class PFindingIntervention(LedgerBaseModel[PFindingInterventionDataDict]):
    patient_finding_interventions: str
    intervention: str

    @classmethod
    def list_type_fields(cls) -> List[str]:
        return P_INTERVENTIONS_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[PFindingInterventionDataDict]:
        return PFindingInterventionDataDict

    @classmethod
    def nested_fields(cls) -> List[str]:
        return P_INTERVENTIONS_MODEL_NESTED_FIELDS
