from lx_dtypes.models.base.app_base_model.ddict.LedgerBaseModelDataDict import (
    LedgerBaseModelDataDict,
)


class PIndicationDataDict(LedgerBaseModelDataDict):
    indication: str
    patient_examination: str
