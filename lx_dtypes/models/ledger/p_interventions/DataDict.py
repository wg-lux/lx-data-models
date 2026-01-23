from typing import List

from lx_dtypes.models.base.app_base_model.ddict.LedgerBaseModelDataDict import (
    LedgerBaseModelDataDict,
)
from lx_dtypes.models.ledger.p_intervention.DataDict import (
    PFindingInterventionDataDict,
)


class PFindingInterventionsDataDict(LedgerBaseModelDataDict):
    patient_finding: str
    patient_finding_interventions: List[PFindingInterventionDataDict]


class SerializedPFindingInterventionsDataDict(LedgerBaseModelDataDict):
    patient_finding: str
    patient_finding_interventions: str
