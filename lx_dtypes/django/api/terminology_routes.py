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
        with _http_errors():
            return service.list_bundles()

    @api.get("/terminology/active/fhir", response=dict[str, Any])
    def export_active_terminology_fhir(request: BaseRequest) -> dict[str, Any]:
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
        with _http_errors():
            return service.export_fhir((module_name.strip(), version.strip()))

    @api.post("/terminology/bundles/import", response=ImportTerminologyBundleResponse)
    def import_terminology_bundle(
        request: BaseRequest,
        file: UploadedFile = File(...),  # noqa: B008 - Ninja request marker
    ) -> ImportTerminologyBundleResponse:
        require_write_access(request)
        with _http_errors():
            result = service.import_zip(file)
        clear_kb_caches()
        return result

    @api.post("/terminology/bundles/select", response=SelectTerminologyBundleResponse)
    def select_terminology_bundle(
        request: BaseRequest,
        payload: SelectTerminologyBundleRequest,
    ) -> SelectTerminologyBundleResponse:
        require_write_access(request)
        with _http_errors():
            return service.select(
                payload.module_name.strip(),
                payload.version.strip(),
                expected_revision=payload.expected_revision,
                on_selected=register_runtime_lookup_tracker,
                clear_application_caches=clear_kb_caches,
            )
