from lx_dtypes.models.base.app_base_model.ddict.LedgerBaseModelDataDict import (
    LedgerBaseModelDataDict,
)
from lx_dtypes.models.contracts.patient_examination_report import (
    ReportJsonObject,
    ReportStatus,
)


class ReportDataDict(LedgerBaseModelDataDict):
    patient_examination: str
    template_name: str
    template_version: str
    template_hash: str
    title: str
    status: ReportStatus
    rendered_text: str
    editor_payload: ReportJsonObject
    patient_context_snapshot: ReportJsonObject
    history_context_snapshot: ReportJsonObject
    version: int
    is_active: bool
    finalized_at: str | None


class SerializedReportDataDict(LedgerBaseModelDataDict):
    patient_examination: str
    template_name: str
    template_version: str
    template_hash: str
    title: str
    status: ReportStatus
    rendered_text: str
    editor_payload: ReportJsonObject
    patient_context_snapshot: ReportJsonObject
    history_context_snapshot: ReportJsonObject
    version: int
    is_active: bool
    finalized_at: str | None
