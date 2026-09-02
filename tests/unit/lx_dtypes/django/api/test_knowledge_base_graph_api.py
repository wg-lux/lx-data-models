from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from django.conf import settings
from django.test import Client

from lx_dtypes.django.api import main as api_main
from lx_dtypes.django.api.lookup_tracker import consume_runtime_lookup_trackers
from lx_dtypes.knowledge_bases import (
    BUILTIN_KNOWLEDGE_BASE_PROVIDER,
    get_packaged_knowledge_base,
)
from lx_dtypes.models.contracts.core_concepts import CoreConceptCollection
from lx_dtypes.models.contracts.knowledge_base import KnowledgeBaseIdentity
from lx_dtypes.models.contracts.knowledge_base_graph import (
    build_examination_reporting_context,
    build_knowledge_base_graph_snapshot,
)
from lx_dtypes.models.interface.DataLoader import DataLoader
from lx_dtypes.models.interface.KnowledgeBaseResolver import (
    clear_knowledge_base_resolver_caches,
)


@pytest.fixture(autouse=True)
def _isolate_runtime_lookup_tracker() -> Any:
    consume_runtime_lookup_trackers()
    yield
    consume_runtime_lookup_trackers()


def _core_concepts() -> dict[str, Any]:
    return CoreConceptCollection.model_validate(
        {
            "module_name": "demo_graph",
            "knowledge_base_module": "demo_graph",
            "knowledge_base_version": "1.2.3",
            "classification": [
                {
                    "name": "lesion_size",
                    "classification_types": ["measurement"],
                    "classification_choices": ["size_value"],
                    "kb_module_name": "demo_findings",
                }
            ],
            "classification_type": [{"name": "measurement"}],
            "classification_choice": [
                {
                    "name": "size_value",
                    "classification_choice_descriptors": ["size_mm"],
                }
            ],
            "classification_choice_descriptor": [
                {
                    "name": "size_mm",
                    "classification_choice_descriptor_type": "numeric",
                    "unit": "millimeter",
                }
            ],
            "examination": [
                {
                    "name": "gastroscopy",
                    "examination_types": ["endoscopy"],
                    "findings": ["polyp"],
                    "indications": ["screening"],
                }
            ],
            "examination_type": [{"name": "endoscopy"}],
            "finding": [
                {
                    "name": "polyp",
                    "finding_types": ["lesion"],
                    "classifications": ["lesion_size"],
                    "interventions": ["biopsy"],
                },
                {
                    "name": "unrelated_finding",
                    "finding_types": ["lesion"],
                },
            ],
            "finding_type": [{"name": "lesion"}],
            "indication": [
                {
                    "name": "screening",
                    "indication_types": ["preventive"],
                }
            ],
            "indication_type": [{"name": "preventive"}],
            "intervention": [{"name": "biopsy", "intervention_types": ["sampling"]}],
            "intervention_type": [{"name": "sampling"}],
            "unit": [{"name": "millimeter", "unit_types": ["length"]}],
            "unit_type": [{"name": "length"}],
            "information_source": [
                {
                    "name": "demo_guideline",
                    "information_source_types": ["guideline"],
                }
            ],
            "information_source_type": [{"name": "guideline"}],
            "citation": [
                {
                    "name": "demo_citation",
                    "citation_key": "demo-2026",
                    "title": "Demo guideline",
                }
            ],
        }
    ).model_dump(mode="json")


def _template_payload(name: str) -> dict[str, Any]:
    return {
        "name": name,
        "name_de": "Gastroskopiebericht",
        "name_en": "Gastroscopy report",
        "description": "Structured report.",
        "version": "1.0.0",
        "examination": "gastroscopy",
        "guideline_references": [],
        "coverage_version": "report_concept_coverage_v1",
        "coverage_concepts": [],
        "report_sections": [],
        "validators": {
            "findings_validators": [
                {
                    "name": "finding_exists",
                    "created_at": datetime.now(UTC),
                    "uuid": str(uuid4()),
                }
            ]
        },
        "lifecycle_status": "published",
        "readiness": {"can_publish": True},
        "issues": [],
    }


class _GraphKb:
    report_template = {  # noqa: RUF012 - immutable test fixture catalog
        "gastroscopy_report": object(),
        "draft_report": object(),
    }

    def export_core_concepts(self) -> dict[str, Any]:
        return _core_concepts()

    def get_report_template_lifecycle_status(self, name: str) -> str:
        return "draft" if name == "draft_report" else "published"

    def export_report_template(self, name: str) -> dict[str, Any]:
        return _template_payload(name)


def test_graph_snapshot_is_deterministic_and_typed() -> None:
    identity = KnowledgeBaseIdentity(
        knowledge_base_module="demo_graph",
        knowledge_base_version="1.2.3",
    )

    first = build_knowledge_base_graph_snapshot(_GraphKb(), identity=identity)
    second = build_knowledge_base_graph_snapshot(_GraphKb(), identity=identity)

    assert first.snapshot_id == second.snapshot_id
    assert first.snapshot_id.startswith("sha256:")
    assert first.declaring_modules == ["demo_findings", "demo_graph"]
    assert [template.name for template in first.report_templates] == [
        "gastroscopy_report"
    ]
    assert any(
        edge.source.name == "gastroscopy"
        and edge.relationship == "has_finding"
        and edge.target.name == "polyp"
        for edge in first.edges
    )
    assert any(
        edge.source.name == "gastroscopy_report"
        and edge.relationship == "for_examination"
        and edge.target.name == "gastroscopy"
        for edge in first.edges
    )


def test_graph_projection_strips_template_source_file_paths() -> None:
    class SourcePathKb(_GraphKb):
        def export_report_template(self, name: str) -> dict[str, Any]:
            payload = _template_payload(name)
            payload["issues"] = [
                {
                    "code": "x001",
                    "source": {
                        "file": "/opt/local/lib/python3.12/site-packages/lx_dtypes/data/foo.yaml",
                        "line": 42,
                    },
                },
                {
                    "code": "x002",
                    "source": [
                        {
                            "file": "/opt/local/lib/python3.12/site-packages/lx_dtypes/data/bar.yaml",
                            "line": 99,
                        },
                    ],
                },
            ]
            return payload

    identity = KnowledgeBaseIdentity(
        knowledge_base_module="demo_graph",
        knowledge_base_version="1.2.3",
    )

    snapshot = build_knowledge_base_graph_snapshot(
        SourcePathKb(),
        identity=identity,
    )
    templates = snapshot.report_templates
    assert [template.name for template in templates] == ["gastroscopy_report"]

    issues = templates[0].issues
    assert issues == [
        {"code": "x001", "source": {"line": 42}},
        {"code": "x002", "source": [{"line": 99}]},
    ]


@pytest.mark.parametrize(
    ("module_name", "module_version", "expected_templates"),
    [
        (
            "dgvs_reporting",
            "0.1.0",
            {
                "colonoscopy_training_basic": "DGVS-AWMF-021-022-v2.1-2025-07",
            },
        ),
        ("coloreg", "0.1.0", {"coloreg_colonoscopy": "1.0.0"}),
        (
            "mst_3_0",
            "3.0.0",
            {
                "mst30_colonoscopy_report": "3.0",
                "mst30_egd_report": "3.0",
                "mst30_enteroscopy_report": "3.0",
                "mst30_ercp_report": "3.0",
                "mst30_eus_report": "3.0",
                "mst30_gastroscopy_report": "3.0",
                "mst30_vce_report": "3.0",
            },
        ),
        (
            "star_upper_gi",
            "0.1.2",
            {
                "star_upper_gi_mini_report_template": "0.1.1",
                "star_upper_gi_standard_report_template": "2025.1",
            },
        ),
    ],
)
def test_packaged_reporting_bundle_builds_versioned_graph_snapshot(
    module_name: str,
    module_version: str,
    expected_templates: dict[str, str],
) -> None:
    kb = DataLoader().load_knowledge_base(module_name)

    snapshot = build_knowledge_base_graph_snapshot(
        kb,
        identity=KnowledgeBaseIdentity(
            knowledge_base_module=module_name,
            knowledge_base_version=module_version,
        ),
    )

    assert {
        template.name: template.version for template in snapshot.report_templates
    } == expected_templates


def test_packaged_provider_registry_serves_full_dgvs_reporting_context(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    descriptor = get_packaged_knowledge_base("dgvs_reporting", "0.1.0")
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "modules": {
                    descriptor.module_name: {
                        descriptor.version: {
                            "sources": [
                                {
                                    "kind": "provider",
                                    "provider": BUILTIN_KNOWLEDGE_BASE_PROVIDER,
                                    "content_sha256": descriptor.content_sha256,
                                }
                            ]
                        }
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        settings,
        "LX_DTYPES_KB_REGISTRY",
        str(registry_path),
        raising=False,
    )
    clear_knowledge_base_resolver_caches()
    try:
        response = Client().get(
            "/base_api/knowledge-bases/dgvs_reporting/0.1.0/examinations/"
            "colonoscopy/reporting-context",
            secure=True,
        )
    finally:
        clear_knowledge_base_resolver_caches()

    assert response.status_code == 200, response.content.decode()
    payload = response.json()
    assert payload["identity"] == {
        "knowledge_base_module": "dgvs_reporting",
        "knowledge_base_version": "0.1.0",
    }
    assert payload["examination_name"] == "colonoscopy"
    assert payload["concepts"]["finding"]
    assert payload["concepts"]["classification"]
    assert [template["name"] for template in payload["report_templates"]] == [
        "colonoscopy_training_basic",
    ]


def test_reporting_context_is_a_closed_examination_projection() -> None:
    snapshot = build_knowledge_base_graph_snapshot(
        _GraphKb(),
        identity=KnowledgeBaseIdentity(
            knowledge_base_module="demo_graph",
            knowledge_base_version="1.2.3",
        ),
    )

    context = build_examination_reporting_context(
        snapshot,
        examination_name="gastroscopy",
    )

    assert context.graph_snapshot_id == snapshot.snapshot_id
    assert context.context_id.startswith("sha256:")
    assert [item.name for item in context.concepts.examination] == ["gastroscopy"]
    assert [item.name for item in context.concepts.finding] == ["polyp"]
    assert [item.name for item in context.concepts.classification] == ["lesion_size"]
    assert [item.name for item in context.concepts.classification_choice] == [
        "size_value"
    ]
    assert [
        item.name for item in context.concepts.classification_choice_descriptor
    ] == ["size_mm"]
    assert [item.name for item in context.concepts.unit] == ["millimeter"]
    assert [item.name for item in context.report_templates] == ["gastroscopy_report"]


def test_graph_and_reporting_context_endpoints_use_exact_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[tuple[str, str | None]] = []

    def load(module_name: str, *, version: str | None = None) -> _GraphKb:
        captured.append((module_name, version))
        return _GraphKb()

    monkeypatch.setattr(api_main, "load_knowledge_base", load)
    client = Client()

    graph_response = client.get(
        "/base_api/knowledge-bases/demo_graph/1.2.3/graph",
        secure=True,
    )
    context_response = client.get(
        "/base_api/knowledge-bases/demo_graph/1.2.3/examinations/"
        "gastroscopy/reporting-context",
        secure=True,
    )

    assert graph_response.status_code == 200
    assert context_response.status_code == 200
    assert captured == [("demo_graph", "1.2.3"), ("demo_graph", "1.2.3")]
    assert graph_response.json()["identity"] == {
        "knowledge_base_module": "demo_graph",
        "knowledge_base_version": "1.2.3",
    }
    assert context_response.json()["examination_name"] == "gastroscopy"
    assert (
        context_response.json()["graph_snapshot_id"]
        == graph_response.json()["snapshot_id"]
    )


def test_reporting_context_endpoint_rejects_unknown_examination(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        api_main,
        "load_knowledge_base",
        lambda *args, **kwargs: _GraphKb(),
    )

    response = Client().get(
        "/base_api/knowledge-bases/demo_graph/1.2.3/examinations/"
        "unknown/reporting-context",
        secure=True,
    )

    assert response.status_code == 404
    assert "unknown" in response.json()["detail"]
