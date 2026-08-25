from typing import TYPE_CHECKING

from lx_dtypes.models.base.app_base_model.ddict.LedgerBaseModelDataDict import (
    LedgerBaseModelDataDict,
)

if TYPE_CHECKING:
    from lx_dtypes.models.ledger.p_finding.DataDict import PFindingDataDict
    from lx_dtypes.models.ledger.p_indication.DataDict import PIndicationDataDict


class PExaminationDataDict(LedgerBaseModelDataDict):
    examiners: list[str]
    examination: str
    knowledge_base_module: str | None
    knowledge_base_version: str | None
    date: str | None
    patient_findings: list["PFindingDataDict"]
    patient_indications: list["PIndicationDataDict"]
    patient: str


class SerializedPExaminationDataDict(LedgerBaseModelDataDict):
    examiners: list[str]
    examination: str
    knowledge_base_module: str | None
    knowledge_base_version: str | None
    date: str | None
    patient_findings: str
    patient_indications: str
    patient: str
