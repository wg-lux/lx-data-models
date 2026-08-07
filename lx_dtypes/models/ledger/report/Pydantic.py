from typing import List, Optional

from pydantic import Field

from lx_dtypes.models.base.app_base_model.pydantic.LedgerBaseModel import (
    LedgerBaseModel,
)
from lx_dtypes.models.contracts.patient_examination_report import (
    ReportJsonObject,
    ReportStatus,
)

from .DataDict import ReportDataDict, SerializedReportDataDict


class Report(LedgerBaseModel[ReportDataDict]):
    patient_examination: str = ""
    template_name: str = ""
    template_version: str = ""
    template_hash: str = ""
    title: str = ""
    status: ReportStatus = "draft"
    rendered_text: str = ""
    editor_payload: ReportJsonObject = Field(default_factory=dict)
    patient_context_snapshot: ReportJsonObject = Field(default_factory=dict)
    history_context_snapshot: ReportJsonObject = Field(default_factory=dict)
    version: int = 1
    is_active: bool = True
    finalized_at: Optional[str] = None

    @classmethod
    def list_type_fields(cls) -> List[str]:
        return []

    @property
    def ddict_class(self) -> type[ReportDataDict]:
        return ReportDataDict

    @classmethod
    def nested_fields(cls) -> List[str]:
        return []

    @property
    def serialized_ddict_class(self) -> type[SerializedReportDataDict]:
        return SerializedReportDataDict

    @classmethod
    def serialized_model_class(cls) -> type["SerializedReport"]:
        return SerializedReport


class SerializedReport(LedgerBaseModel[SerializedReportDataDict]):
    patient_examination: str = ""
    template_name: str = ""
    template_version: str = ""
    template_hash: str = ""
    title: str = ""
    status: ReportStatus = "draft"
    rendered_text: str = ""
    editor_payload: ReportJsonObject = Field(default_factory=dict)
    patient_context_snapshot: ReportJsonObject = Field(default_factory=dict)
    history_context_snapshot: ReportJsonObject = Field(default_factory=dict)
    version: int = 1
    is_active: bool = True
    finalized_at: Optional[str] = None

    @classmethod
    def list_type_fields(cls) -> List[str]:
        return []

    @property
    def ddict_class(self) -> type[SerializedReportDataDict]:
        return SerializedReportDataDict

    @classmethod
    def nested_fields(cls) -> List[str]:
        return []
