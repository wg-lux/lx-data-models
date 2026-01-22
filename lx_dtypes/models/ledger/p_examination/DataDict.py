from typing import TYPE_CHECKING, List, Optional

from lx_dtypes.models.base.app_base_model.ddict.LedgerBaseModelDataDict import (
    LedgerBaseModelDataDict,
)

if TYPE_CHECKING:
    from lx_dtypes.models.ledger.p_finding.DataDict import PFindingDataDict
    from lx_dtypes.models.ledger.p_indication.DataDict import PIndicationDataDict


class PExaminationDataDict(LedgerBaseModelDataDict):
    examiners: List[str]
    examination: str
    date: Optional[str]
    patient_findings: List["PFindingDataDict"]
    patient_indications: List["PIndicationDataDict"]
    patient: str


class SerializedPExaminationDataDict(LedgerBaseModelDataDict):
    examiners: List[str]
    examination: str
    date: Optional[str]
    patient_findings: str
    patient_indications: str
    patient: str
