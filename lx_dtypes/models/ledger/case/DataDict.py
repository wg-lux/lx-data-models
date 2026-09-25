from typing import TYPE_CHECKING

from lx_dtypes.models.base.app_base_model.ddict.LedgerBaseModelDataDict import (
    LedgerBaseModelDataDict,
)

if TYPE_CHECKING:
    from lx_dtypes.models.ledger.p_examination.DataDict import PExaminationDataDict


class CaseDataDict(LedgerBaseModelDataDict):
    case_id: str
    patient: str
    admission_date: str
    leave_date: str | None
    patient_examinations: list["PExaminationDataDict"]
    report_ids: list[str]


class SerializedCaseDataDict(LedgerBaseModelDataDict):
    case_id: str
    patient: str
    admission_date: str
    leave_date: str | None
    patient_examinations: str
    report_ids: str
