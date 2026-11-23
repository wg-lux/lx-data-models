"""HTTP adapter. Storage and knowledge-base operations live in the service."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

from ninja import File, NinjaAPI, Router
from ninja.errors import HttpError
from ninja.files import UploadedFile

from lx_dtypes.terminology.lookup_tracker import register_runtime_lookup_tracker
from lx_dtypes.terminology.terminology_schemas import (
    ImportTerminologyBundleResponse,
    ReportTemplateCatalogResponse,
    SelectTerminologyBundleRequest,
    SelectTerminologyBundleResponse,
    TerminologyBundleListResponse,
)
from lx_dtypes.terminology.terminology_service import (
    TerminologyError,
    TerminologyService,
)

from .request_types import BaseRequest


@contextmanager
def _http_errors() -> Iterator[None]:
    try:
        yield
    except TerminologyError as exc:
        raise HttpError(exc.status, str(exc)) from exc


def register_terminology_routes(
    api: NinjaAPI | Router,
    *,
    service: TerminologyService,
    clear_kb_caches: Callable[[], None],
    authenticate_request_user: Callable[[BaseRequest], Any | None] | None = None,
    terminology_write_access_allowed: Callable[[object], bool] | None = None,
) -> None:
    def require_write_access(request: BaseRequest) -> None:
        if (
            authenticate_request_user is None
            or terminology_write_access_allowed is None
        ):
            raise HttpError(403, "Terminology writes are not configured.")
        actor = authenticate_request_user(request)
        if actor is None:
            raise HttpError(401, "Authentication is required.")
        if not terminology_write_access_allowed(actor):
            raise HttpError(403, "Terminology write access is required.")

    @api.get("/terminology/bundles", response=TerminologyBundleListResponse)
    def list_terminology_bundles(request: BaseRequest) -> TerminologyBundleListResponse:
        """List the installed terminology bundles and their versions.

        The response names the active bundle and the registry ``revision``
        that ``select`` expects. No authentication is required.
        """
        with _http_errors():
            return service.list_bundles()

    @api.get("/terminology/report-templates", response=ReportTemplateCatalogResponse)
    def list_report_template_catalog(
        request: BaseRequest, examination: str | None = None
    ) -> ReportTemplateCatalogResponse:
        """List the report templates of all installed terminology bundles.

        ``examination`` restricts the list to templates for that examination. No
        authentication is required.
        """
        with _http_errors():
            return service.list_report_templates(examination=examination)

    @api.get("/terminology/active/fhir", response=dict[str, Any])
    def export_active_terminology_fhir(request: BaseRequest) -> dict[str, Any]:
        """Export the active terminology bundle as a FHIR Bundle.

        No authentication is required.

        Errors: ``404`` if no bundle is active, ``409`` if the bundle cannot
        be exported.
        """
        with _http_errors():
            return service.export_fhir()

    @api.get(
        "/terminology/bundles/{module_name}/{version}/fhir", response=dict[str, Any]
    )
    def export_terminology_bundle_fhir(
        request: BaseRequest,
        module_name: str,
        version: str,
    ) -> dict[str, Any]:
        """Export one installed terminology bundle version as a FHIR Bundle.

        No authentication is required.

        Errors: ``404`` if the bundle version is not installed, ``409`` if it
        cannot be exported.
        """
        with _http_errors():
            return service.export_fhir((module_name.strip(), version.strip()))

    @api.post("/terminology/bundles/import", response=ImportTerminologyBundleResponse)
    def import_terminology_bundle(
        request: BaseRequest,
        file: File[UploadedFile],
    ) -> ImportTerminologyBundleResponse:
        """Install a terminology bundle from an uploaded ZIP archive.

        The archive is validated before installation. Importing does not activate
        the bundle; use ``select`` for that.

        Authentication: requires terminology write access, which the host must
        configure.

        Errors: ``401`` without credentials, ``403`` without write access or when
        writes are not configured, ``400`` for an invalid upload.
        """
        require_write_access(request)
        with _http_errors():
            if file.file is None:
                raise HttpError(400, "Uploaded file has no content stream.")
            result = service.import_zip(file.file)
        clear_kb_caches()
        return result

    @api.post("/terminology/bundles/select", response=SelectTerminologyBundleResponse)
    def select_terminology_bundle(
        request: BaseRequest,
        payload: SelectTerminologyBundleRequest,
    ) -> SelectTerminologyBundleResponse:
        """Make an installed terminology bundle version the active one.

        ``expected_revision`` guards against concurrent changes: the selection
        fails if the active state changed since the caller read it. Application
        caches are cleared after the switch.

        Authentication: requires terminology write access, which the host must
        configure.

        Errors: ``401`` without credentials, ``403`` without write access or when
        writes are not configured, ``404`` if the version is not installed,
        ``409`` if ``expected_revision`` is stale or the loaded bundle reports a
        different identity.
        """
        require_write_access(request)
        with _http_errors():
            return service.select(
                payload.module_name.strip(),
                payload.version.strip(),
                expected_revision=payload.expected_revision,
                on_selected=register_runtime_lookup_tracker,
                clear_application_caches=clear_kb_caches,
            )
