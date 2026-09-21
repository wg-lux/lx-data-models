# ruff: noqa: FLY002 - line lists keep embedded YAML fixtures readable

from __future__ import annotations

import sys
import zipfile
from collections.abc import Iterator
from io import BytesIO
from pathlib import Path
from types import ModuleType
from uuid import uuid4

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import clear_url_caches, path
from ninja import NinjaAPI
from pytest_django.fixtures import SettingsWrapper

from lx_dtypes.django.api.knowledge_base_graph_routes import (
    KnowledgeBaseGraphRouteCache,
    register_knowledge_base_graph_routes,
)
from lx_dtypes.django.api.terminology_routes import register_terminology_routes
from lx_dtypes.terminology import terminology_loader as central


@pytest.fixture
def editor_client(
    terminology_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    settings: SettingsWrapper,
) -> Iterator[Client]:
    """Register writes and graph reads against one isolated central service."""
    service = central.get_terminology_service()
    assert service.registry_path == terminology_root / "registry.json"
    graph_cache = KnowledgeBaseGraphRouteCache()
    api = NinjaAPI(
        urls_namespace=f"editor-integration-{uuid4().hex}",
        docs_url=None,
        openapi_url=None,
    )
    register_terminology_routes(
        api,
        service=service,
        clear_kb_caches=graph_cache.clear,
        authenticate_request_user=lambda request: request.headers.get("X-Test-Actor"),
        terminology_write_access_allowed=lambda actor: actor == "editor",
    )
    register_knowledge_base_graph_routes(
        api,
        graph_cache=graph_cache,
        load_module_kb=central.load_module_kb,
    )
    module_name = f"_editor_integration_urls_{uuid4().hex}"
    urlconf = ModuleType(module_name)
    monkeypatch.setattr(
        urlconf, "urlpatterns", [path("base_api/", api.urls)], raising=False
    )
    monkeypatch.setitem(sys.modules, module_name, urlconf)
    settings.ROOT_URLCONF = module_name
    settings.ALLOWED_HOSTS = ["testserver"]
    settings.MIDDLEWARE = []
    clear_url_caches()
    try:
        yield Client()
    finally:
        clear_url_caches()
        graph_cache.clear()


def _editor_graph_bundle_zip() -> bytes:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "editor_graph_bundle/config.yaml",
            "\n".join(
                [
                    "name: editor_graph_bundle",
                    "version: 1.2.3",
                    "medical_field: gastroenterology",
                    "modules:",
                    "  - lx_findings",
                    "  - lx_examinations",
                    "depends_on: []",
                ]
            )
            + "\n",
        )
        archive.writestr(
            "editor_graph_bundle/lx_findings/config.yaml",
            "\n".join(
                [
                    "name: lx_findings",
                    "version: 1.0.0",
                    "modules: []",
                    "depends_on: []",
                    "data:",
                    "  dirs:",
                    "    - ./data",
                ]
            )
            + "\n",
        )
        archive.writestr(
            "editor_graph_bundle/lx_findings/data/findings.yaml",
            "\n".join(
                [
                    "- model: finding",
                    "  name: editor_finding",
                    "  description: Finding published by the terminology editor.",
                ]
            )
            + "\n",
        )
        archive.writestr(
            "editor_graph_bundle/lx_examinations/config.yaml",
            "\n".join(
                [
                    "name: lx_examinations",
                    "version: 1.0.0",
                    "modules: []",
                    "depends_on:",
                    "  - lx_findings",
                    "data:",
                    "  dirs:",
                    "    - ./data",
                ]
            )
            + "\n",
        )
        archive.writestr(
            "editor_graph_bundle/lx_examinations/data/examinations.yaml",
            "\n".join(
                [
                    "- model: examination",
                    "  name: editor_examination",
                    "  description: Examination published by the terminology editor.",
                    "  findings:",
                    "    - editor_finding",
                ]
            )
            + "\n",
        )
    return buffer.getvalue()


def test_editor_zip_import_is_immediately_available_through_graph_api(
    editor_client: Client,
    terminology_root: Path,
) -> None:
    client = editor_client
    import_response = client.post(
        "/base_api/terminology/bundles/import",
        data={
            "file": SimpleUploadedFile(
                "editor_graph_bundle.zip",
                _editor_graph_bundle_zip(),
                content_type="application/zip",
            )
        },
        secure=True,
        headers={"X-Test-Actor": "editor"},
    )

    assert import_response.status_code == 200, import_response.content.decode()
    assert (terminology_root / "registry.json").is_file()
    assert central.get_terminology_service().active_identity() is None
    assert import_response.json()["imported"] == {
        "module_name": "editor_graph_bundle",
        "version": "1.2.3",
        "medical_field": "gastroenterology",
        "is_active": False,
    }
    assert (
        client.get("/base_api/terminology/bundles", secure=True).json()["active"]
        is None
    )

    graph_response = client.get(
        "/base_api/knowledge-bases/editor_graph_bundle/1.2.3/graph",
        secure=True,
    )
    context_response = client.get(
        "/base_api/knowledge-bases/editor_graph_bundle/1.2.3/examinations/"
        "editor_examination/reporting-context",
        secure=True,
    )

    assert graph_response.status_code == 200
    graph = graph_response.json()
    assert graph["contract_version"] == "knowledge_base_graph_v1"
    assert graph["identity"] == {
        "knowledge_base_module": "editor_graph_bundle",
        "knowledge_base_version": "1.2.3",
    }
    assert any(
        edge
        == {
            "source": {"kind": "examination", "name": "editor_examination"},
            "relationship": "has_finding",
            "target": {"kind": "finding", "name": "editor_finding"},
        }
        for edge in graph["edges"]
    )

    assert context_response.status_code == 200
    context = context_response.json()
    assert context["contract_version"] == "knowledge_base_graph_v1"
    assert context["graph_snapshot_id"] == graph["snapshot_id"]
    assert context["examination_name"] == "editor_examination"
    assert [item["name"] for item in context["concepts"]["finding"]] == [
        "editor_finding"
    ]


def test_editor_zip_import_requires_an_authorized_actor(
    editor_client: Client,
    terminology_root: Path,
) -> None:
    for headers, expected_status in (({}, 401), ({"X-Test-Actor": "reader"}, 403)):
        response = editor_client.post(
            "/base_api/terminology/bundles/import",
            data={
                "file": SimpleUploadedFile(
                    "editor_graph_bundle.zip",
                    _editor_graph_bundle_zip(),
                    content_type="application/zip",
                )
            },
            secure=True,
            headers=headers,
        )
        assert response.status_code == expected_status
    assert not (terminology_root / "registry.json").exists()
    assert not (terminology_root / "terminology-packages").exists()
