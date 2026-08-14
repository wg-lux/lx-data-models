from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from django.test import Client
import pytest

from lx_dtypes.django.api import main as api_main
from lx_dtypes.django.api.lookup_tracker import consume_runtime_lookup_trackers
from lx_dtypes.models.contracts.core_concepts import CoreConceptCollection
from lx_dtypes.models.contracts.knowledge_base import KnowledgeBaseIdentity
from lx_dtypes.models.contracts.knowledge_base_graph import (
    build_examination_reporting_context,
    build_knowledge_base_graph_snapshot,
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
    report_template = {
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
