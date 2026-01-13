from lx_dtypes.models.base.app_base_model.ddict.LedgerBaseModelDataDict import (
    LedgerBaseModelDataDict,
)


class PFindingDataDict(LedgerBaseModelDataDict):
    finding: str
    patient_examination: str
