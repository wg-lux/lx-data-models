from lx_dtypes.models.base.app_base_model.ddict.LedgerBaseModelDataDict import (
    LedgerBaseModelDataDict,
)
from lx_dtypes.models.base.app_base_model.ddict.PersonDataDict import (
    PersonDataDict,
)


class PatientDataDict(LedgerBaseModelDataDict, PersonDataDict):
    center: str
