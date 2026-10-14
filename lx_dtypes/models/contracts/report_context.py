from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator

from .document_type import DocumentType


class ReportContext(BaseModel):
    patient_examination_id: int
    patient_id: int
    document_type: DocumentType
    anonymized_text: str
    report_template_name: str | None = None
    report_template_version: str | None = None
    language: str | None = None
    examination_hash: str | None = None
    patient_hash: str | None = None
    source_pdf_id: int | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("anonymized_text", mode="before")
    @classmethod
    def normalize_text(cls, value: str | float | bool | None) -> str:
        if value is None:
            return ""
        return str(value)


__all__ = ["ReportContext"]
