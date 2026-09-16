"""The existing terminology request and response contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TerminologyBundleVersion(BaseModel):
    module_name: str
    version: str
    medical_field: str | None = None
    is_active: bool = False


class TerminologyBundleListResponse(BaseModel):
    revision: str
    active: TerminologyBundleVersion | None
    bundles: list[TerminologyBundleVersion]


class SelectTerminologyBundleRequest(BaseModel):
    module_name: str
    version: str
    expected_revision: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")


class SelectTerminologyBundleResponse(BaseModel):
    ok: bool
    revision: str
    active: TerminologyBundleVersion
    counts: dict[str, int]


class ImportTerminologyBundleResponse(BaseModel):
    ok: bool
    revision: str
    imported: TerminologyBundleVersion
    counts: dict[str, int]
