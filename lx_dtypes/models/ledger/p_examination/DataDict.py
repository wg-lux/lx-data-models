from typing import TYPE_CHECKING, List, Optional

from lx_dtypes.models.base.app_base_model.ddict.LedgerBaseModelDataDict import (
    LedgerBaseModelDataDict,
)

if TYPE_CHECKING:
    from lx_dtypes.models.ledger.p_finding.DataDict import PFindingDataDict


class PExaminationDataDict(LedgerBaseModelDataDict):
    examiners: List[str]
    examination: str
    date: Optional[str]
    # TODO: Full implementation with nested DataDicts
    patient_findings: List["PFindingDataDict"]
    # patient_indications: List[str]  # List[PIndicationDataDict] in full implementation
