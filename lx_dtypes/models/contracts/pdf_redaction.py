from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, field_validator


class PdfRedactionBox(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: float
    y: float
    width: float
    height: float

    @field_validator("x", "y", "width", "height")
    @classmethod
    def validate_normalized_coordinate(cls, value: float) -> float:
        if value < 0 or value > 1:
            raise ValueError("value must be within [0, 1]")
        return value

    @field_validator("height", "width")
    @classmethod
    def validate_positive_size(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("value must be > 0")
        return value


class PdfRedactionPage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page: int
    boxes: list[PdfRedactionBox]

    @field_validator("page")
    @classmethod
    def validate_page(cls, value: int) -> int:
        if value < 1:
            raise ValueError("page must be an integer >= 1")
        return value


class PdfRedactionManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int
    normalized: Literal[True]
    pages: list[PdfRedactionPage]

    @field_validator("version")
    @classmethod
    def validate_version(cls, value: int) -> int:
        if value < 1:
            raise ValueError("version must be an integer >= 1")
        return value

    @field_validator("pages")
    @classmethod
    def validate_pages(cls, value: list[PdfRedactionPage]) -> list[PdfRedactionPage]:
        for page_entry in value:
            for box in page_entry.boxes:
                if box.x + box.width > 1 or box.y + box.height > 1:
                    raise ValueError("all boxes must fit inside normalized page bounds")
        return value


class PdfRedactionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_type: Literal["raw", "processed"]
    redaction_manifest: PdfRedactionManifest
    note: str = ""
    client_source_sha256: str = ""

    @field_validator("redaction_manifest", mode="before")
    @classmethod
    def parse_manifest(cls, value: object) -> object:
        if isinstance(value, str):
            payload = value.strip()
            if not payload:
                raise ValueError("redaction_manifest must not be empty")
            parsed = json.loads(payload)
            if not isinstance(parsed, dict):
                raise ValueError("redaction_manifest must be a JSON object")
            return parsed
        return value

    @field_validator("note", mode="before")
    @classmethod
    def normalize_note(cls, value: Any) -> str:
        if value in (None, ""):
            return ""
        return str(value).strip()

    @field_validator("client_source_sha256", mode="before")
    @classmethod
    def normalize_client_source_sha256(cls, value: Any) -> str:
        if value in (None, ""):
            return ""
        return str(value).strip().lower()

    @field_validator("client_source_sha256")
    @classmethod
    def validate_client_source_sha256(cls, value: str) -> str:
        if not value:
            return value
        if len(value) != 64:
            raise ValueError("client_source_sha256 must contain 64 hex chars")
        if any(ch not in "0123456789abcdef" for ch in value):
            raise ValueError("client_source_sha256 must be lowercase hex")
        return value


class PdfRedactionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file_id: int
    revision_id: int
    processed_stream_url: str
    status: str
    anonymization_validated: bool
    updated_at: str


__all__ = [
    "PdfRedactionBox",
    "PdfRedactionManifest",
    "PdfRedactionPage",
    "PdfRedactionRequest",
    "PdfRedactionResponse",
]
