from __future__ import annotations

import zipfile
from collections.abc import Iterator
from io import BytesIO
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
import pytest

from lx_dtypes.models.interface.KnowledgeBaseResolver import (
    clear_knowledge_base_resolver_caches,
)


@pytest.fixture(autouse=True)
def _isolate_knowledge_base_registry(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[None]:
    monkeypatch.delenv("LX_DTYPES_KB_REGISTRY", raising=False)
    monkeypatch.delenv("LX_DTYPES_TERMINOLOGY_IMPORT_ROOT", raising=False)
    clear_knowledge_base_resolver_caches()
    yield
    clear_knowledge_base_resolver_caches()


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
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    registry_path = tmp_path / "kb_registry.json"
    import_root = tmp_path / "terminology-packages"
    monkeypatch.setenv("LX_DTYPES_KB_REGISTRY", str(registry_path))
    monkeypatch.setenv("LX_DTYPES_TERMINOLOGY_IMPORT_ROOT", str(import_root))

    client = Client()
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
    )

    assert import_response.status_code == 200
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
