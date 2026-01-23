from typing import List

from pydantic import Field

from lx_dtypes.models.base.app_base_model.pydantic.LedgerBaseModel import (
    LedgerBaseModel,
)
from lx_dtypes.models.ledger.p_intervention.Pydantic import (
    PFindingIntervention,
)
from lx_dtypes.names import (
    P_INTERVENTIONS_MODEL_LIST_TYPE_FIELDS,
    P_INTERVENTIONS_MODEL_NESTED_FIELDS,
)

from .DataDict import (
    PFindingInterventionsDataDict,
    SerializedPFindingInterventionsDataDict,
)


class PFindingInterventions(LedgerBaseModel[PFindingInterventionsDataDict]):
    patient_finding: str

    patient_finding_interventions: List[PFindingIntervention] = Field(
        default_factory=list
    )

    @classmethod
    def list_type_fields(cls) -> List[str]:
        return P_INTERVENTIONS_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[PFindingInterventionsDataDict]:
        return PFindingInterventionsDataDict

    @classmethod
    def nested_fields(cls) -> List[str]:
        return P_INTERVENTIONS_MODEL_NESTED_FIELDS

    @property
    def serialized_ddict_class(self) -> type[SerializedPFindingInterventionsDataDict]:
        return SerializedPFindingInterventionsDataDict

    @classmethod
    def serialized_model_class(cls) -> type["SerializedPFindingInterventions"]:
        return SerializedPFindingInterventions


class SerializedPFindingInterventions(
    LedgerBaseModel[SerializedPFindingInterventionsDataDict]
):
    patient_finding: str
    patient_finding_interventions: str = ""

    @classmethod
    def list_type_fields(cls) -> List[str]:
        return P_INTERVENTIONS_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[SerializedPFindingInterventionsDataDict]:
        return SerializedPFindingInterventionsDataDict

    @classmethod
    def nested_fields(cls) -> List[str]:
        return []
