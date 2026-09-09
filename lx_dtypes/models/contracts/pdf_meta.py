from __future__ import annotations

from datetime import date, time

from pydantic import BaseModel, ConfigDict, Field


class PdfTypeSummaryPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    name: str = Field(min_length=1)
    patient_info_line: str
    endoscope_info_line: str
    examiner_info_line: str
    cut_off_above_lines: list[str] = Field(default_factory=list)
    cut_off_below_lines: list[str] = Field(default_factory=list)


class PdfMetaPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    pdf_type: str = Field(min_length=1)
    date: date
    time: time
    pdf_hash: str = Field(min_length=1)


__all__ = ["PdfMetaPayload", "PdfTypeSummaryPayload"]
