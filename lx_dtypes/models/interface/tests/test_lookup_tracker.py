from __future__ import annotations

import pytest

from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase
from lx_dtypes.models.knowledge_base.classification.Classification import (
    Classification,
)


def test_lookup_tracker_counts_knowledge_base_object_lookups(
    knowledge_base_fixture: KnowledgeBase,
    classification_fixture: Classification,
) -> None:
    kb = knowledge_base_fixture.model_copy(deep=True)
    kb.classification = {"known_classification": classification_fixture}

    resolved = kb.get_classification("known_classification")
    assert resolved is classification_fixture

    with pytest.raises(KeyError):
        kb.get_classification("missing_classification")

    status = kb.get_report_template_lifecycle_status("missing_template")
    assert status == "published"

    summary = kb.get_lookup_tracker_summary()
    assert summary["total_lookup_count"] == 3

    edge_counts = summary["edge_counts"]
    assert {
        "source": "knowledge_base",
        "target": "classification",
        "lookup_count": 2,
    } in edge_counts
    assert {
        "source": "knowledge_base",
        "target": "report_template_lifecycle_status",
        "lookup_count": 1,
    } in edge_counts

    key_counts = summary["key_counts"]
    assert {
        "source": "knowledge_base",
        "target": "classification",
        "key": "missing_classification",
        "found": False,
        "lookup_count": 1,
    } in key_counts


def test_lookup_tracker_graph_exports_and_snomed_comparison(
    knowledge_base_fixture: KnowledgeBase,
    classification_fixture: Classification,
) -> None:
    kb = knowledge_base_fixture.model_copy(deep=True)
    kb.classification = {"known_classification": classification_fixture}

    kb.get_classification("known_classification")
    kb.get_classification("known_classification")

    mermaid = kb.export_lookup_tracker_mermaid()
    dot = kb.export_lookup_tracker_dot()
    assert "graph LR" in mermaid
    assert "classification" in mermaid
    assert "digraph knowledge_base_lookup_graph {" in dot
    assert '"knowledge_base" -> "classification" [label="2"];' in dot

    comparison = kb.compare_lookup_performance_to_snomed(
        snomed_lookup_count=4,
        lx_elapsed_seconds=0.20,
        snomed_elapsed_seconds=0.40,
    )
    assert comparison["lx_lookup_count"] == 2
    assert comparison["snomed_lookup_count"] == 4
    assert comparison["lookup_count_ratio_lx_over_snomed"] == 0.5
    assert comparison["elapsed_time_ratio_lx_over_snomed"] == 0.5

    kb.reset_lookup_tracker()
    assert kb.get_lookup_tracker_summary()["total_lookup_count"] == 0
