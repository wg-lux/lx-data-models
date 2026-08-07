from __future__ import annotations

from typing import Final

from pydantic import BaseModel, ConfigDict, Field

from .json_types import JsonNull, JsonValue
from .patient_examination_report import ReportJsonObject, ReportStatus


type ReportMetaJsonValue = (
    JsonValue
    | JsonNull
    | list["ReportMetaJsonValue"]
    | dict[str, "ReportMetaJsonValue"]
)
type ReportMetaJsonObject = dict[str, ReportMetaJsonValue]


class Report(BaseModel):
    """Canonical contract shape for report records in the medical ledger."""

    model_config = ConfigDict(extra="forbid")

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
    finalized_at: str | None = None


class SerializedReport(Report):
    """Ledger serialized report contract."""


ReportVersion: Final = "v1"
ReportPayload = Report

__all__: list[str] = [
    "Report",
    "SerializedReport",
    "ReportPayload",
    "ReportMetaJsonObject",
    "ReportMetaJsonValue",
    "ReportVersion",
]
