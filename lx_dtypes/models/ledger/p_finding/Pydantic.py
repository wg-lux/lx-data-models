from typing import List

from pydantic import Field

from lx_dtypes.models.base.app_base_model.pydantic.LedgerBaseModel import (
    LedgerBaseModel,
)
from lx_dtypes.models.ledger.p_finding_classifications.Pydantic import (
    PFindingClassifications,
)
from lx_dtypes.models.ledger.p_interventions.Pydantic import (
    PFindingInterventions,
)
from lx_dtypes.names import (
    P_FINDING_MODEL_LIST_TYPE_FIELDS,
    P_FINDING_MODEL_NESTED_FIELDS,
)

from .DataDict import (
    PFindingDataDict,
)


class PFinding(LedgerBaseModel[PFindingDataDict]):
    finding: str
    patient_examination: str
    patient_finding_classifications: List[PFindingClassifications] = Field(
        default_factory=list
    )
    patient_finding_interventions: List[PFindingInterventions] = Field(
        default_factory=list
    )

    @classmethod
    def list_type_fields(cls) -> List[str]:
        return P_FINDING_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[PFindingDataDict]:
        return PFindingDataDict

    @classmethod
    def nested_fields(cls) -> List[str]:
        return P_FINDING_MODEL_NESTED_FIELDS
