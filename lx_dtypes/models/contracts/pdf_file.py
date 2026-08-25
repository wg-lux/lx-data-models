# lx_dtypes/models/contracts/pdf_file.py
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from lx_dtypes.models.contracts.json_types import JsonNull, JsonValue

type FrameSourceMode = Literal["raw", "anonymized"]

type AnonymVideoFile = bytes

type PdfFileMetaJsonValue = JsonValue | JsonNull

type PdfFileMetaJsonObject = dict[str, PdfFileMetaJsonValue]

type PdfFileId = int | None


class PdfFileIdentityPayload(BaseModel):
    """Stable identity/reference fields for a PDF file-like object."""

    model_config = ConfigDict(extra="ignore", frozen=True, strict=True)

    pk: int | None = Field(default=None, ge=1)
    id: int | None = Field(default=None, ge=1)
    pdf_hash: str = Field(min_length=1)
    original_file_name: str | None = None

    @field_validator("id", mode="after")
    @classmethod
    def _id_or_pk(cls, value: int | None, info: ValidationInfo) -> int | None:
        return value


class PdfFileStoragePayload(BaseModel):
    """Storage and filename metadata that is safe to pass across boundaries."""

    model_config = ConfigDict(extra="ignore", frozen=True, strict=True)

    storage_mode: str = ""
    raw_pdf_relative_path: str = ""
    anonymized_pdf_relative_path: str = ""
    has_raw_pdf: bool = False
    is_anonymized: bool = False


class PdfFileContextPayload(BaseModel):
    """Context identifiers that stay in Django but are passed as stable references."""

    model_config = ConfigDict(extra="ignore", frozen=True, strict=True)

    pdf_type_id: PdfFileId = None
    center_id: PdfFileId = None
    examination_id: PdfFileId = None
    examiner_id: PdfFileId = None
    patient_id: PdfFileId = None
    sensitive_meta_id: PdfFileId = None


class PdfFileProcessingStatePayload(BaseModel):
    """Workflow flags for report processing and anonymization."""

    model_config = ConfigDict(extra="ignore", frozen=True, strict=True)

    state_report_processing_required: bool = True
    state_report_processed: bool = False


class PdfFilePayload(
    PdfFileIdentityPayload,
    PdfFileStoragePayload,
    PdfFileContextPayload,
    PdfFileProcessingStatePayload,
):
    """Serializable PDF file contract without Django ORM relations or methods."""

    model_config = ConfigDict(extra="ignore", frozen=True, strict=True)

    uploaded_at: datetime | None = None
    date_created: datetime | None = None
    date_modified: datetime | None = None
    text: str | None = None
    anonymized_text: str | None = None
    raw_meta: PdfFileMetaJsonObject | None = None


__all__ = [
    "FrameSourceMode",
    "PdfFileContextPayload",
    "PdfFileIdentityPayload",
    "PdfFileMetaJsonObject",
    "PdfFileMetaJsonValue",
    "PdfFilePayload",
    "PdfFileProcessingStatePayload",
    "PdfFileStoragePayload",
]
