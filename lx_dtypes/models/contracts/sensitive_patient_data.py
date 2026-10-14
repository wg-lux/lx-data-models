from __future__ import annotations

from typing import TypedDict


class SensitiveMetaReportData(TypedDict):
    id: int | None
    patient_first_name: str
    patient_last_name: str
    patient_dob: str
    patient_gender: str
    examination_date: str
    center_name: str
    endoscope_type: str
    endoscope_sn: str
    is_verified: bool
    tags: list[str]
    validation_comment: str


class VoPPatientDataVideoPayload(TypedDict):
    id: int | None
    sensitive_meta_id: int | None
    text: str
    anonymized_text: str
    report_meta: SensitiveMetaReportData | None
    status: str
    error: bool


class VoPPatientDataPdfPayload(TypedDict):
    id: int | None
    sensitive_meta_id: int | None
    text: str
    anonymized_text: str
    report_meta: SensitiveMetaReportData | None
    status: str
    error: bool
    pdf_stream_url: str


__all__ = [
    "SensitiveMetaReportData",
    "VoPPatientDataPdfPayload",
    "VoPPatientDataVideoPayload",
]
