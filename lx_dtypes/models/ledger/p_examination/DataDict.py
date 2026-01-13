from typing import List, Optional

from lx_dtypes.models.base.app_base_model.ddict.LedgerBaseModelDataDict import (
    LedgerBaseModelDataDict,
)


class PExaminationDataDict(LedgerBaseModelDataDict):
    examiners: List[str]
    examination: str
    date: Optional[str]
    # TODO: Full implementation with nested DataDicts
    # patient_findings: List[str]  # List[PFindingDataDict] in full implementation
    # patient_indications: List[str]  # List[PIndicationDataDict] in full implementation
