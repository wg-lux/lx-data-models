"""The existing terminology request and response contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from lx_dtypes.models.contracts.package_kind import PackageKind
from lx_dtypes.models.model import DtypesModel


class TerminologyBundleVersion(DtypesModel):
    module_name: str
    version: str
    medical_field: str | None = None
    # ``None`` means unclassified; consumers must not treat it as terminology.
    package_kind: PackageKind | None = None
    # declared: registry/config.yaml; catalog: shipped release; migrated: inferred
    # from the package's own records (not persisted); None: unclassified.
    package_kind_source: Literal["declared", "catalog", "migrated"] | None = None
    is_active: bool = False


class TerminologyBundleListResponse(DtypesModel):
    revision: str
    active: TerminologyBundleVersion | None
    bundles: list[TerminologyBundleVersion]


class SelectTerminologyBundleRequest(DtypesModel):
    module_name: str
    version: str
    expected_revision: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")


class SelectTerminologyBundleResponse(DtypesModel):
    ok: bool
    revision: str
    active: TerminologyBundleVersion
    counts: dict[str, int]


class ImportTerminologyBundleResponse(DtypesModel):
    ok: bool
    revision: str
    imported: TerminologyBundleVersion
    counts: dict[str, int]


class ReportTemplateCatalogTemplate(DtypesModel):
    name: str
    version: str | None
    examination: str
    name_de: str | None = None
    name_en: str | None = None


class ReportTemplateCatalogBundle(TerminologyBundleVersion):
    templates: list[ReportTemplateCatalogTemplate]
    error: str | None = None


class ReportTemplateCatalogResponse(DtypesModel):
    revision: str
    bundles: list[ReportTemplateCatalogBundle]
