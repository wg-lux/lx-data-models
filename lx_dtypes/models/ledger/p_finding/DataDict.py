from lx_dtypes.models.base.app_base_model.ddict.LedgerBaseModelDataDict import (
    LedgerBaseModelDataDict,
)
from lx_dtypes.models.ledger.p_finding_classifications.DataDict import (
    PFindingClassificationsDataDict,
)


class PFindingDataDict(LedgerBaseModelDataDict):
    finding: str
    patient_examination: str
    patient_finding_classifications: list[PFindingClassificationsDataDict]
