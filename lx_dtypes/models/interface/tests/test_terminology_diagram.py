from __future__ import annotations

from types import SimpleNamespace

from lx_dtypes.models.interface.TerminologyDiagram import build_terminology_graph
from lx_dtypes.models.knowledge_base.report_template import FindingsValidator


def test_terminology_graph_links_findings_classifications_and_rules() -> None:
    kb = SimpleNamespace(
        examination={
            "colonoscopy": SimpleNamespace(
                name="colonoscopy",
                name_de="Koloskopie",
                findings=["colon_polyp"],
            )
        },
        finding={
            "colon_polyp": SimpleNamespace(
                name="colon_polyp",
                name_de="Kolonpolyp",
                classifications=["lesion_size_mm", "lst"],
                interventions=[],
                caused_by_interventions=[],
            )
        },
        classification={
            "lesion_size_mm": SimpleNamespace(
                name="lesion_size_mm",
                name_de="Groesse",
                classification_choices=["size_numeric"],
            ),
            "lst": SimpleNamespace(
                name="lst",
                name_de="Laterally spreading tumor",
                classification_choices=[],
            ),
        },
        classification_choice={
            "size_numeric": SimpleNamespace(
                name="size_numeric",
                classification_choice_descriptors=["size_value"],
            )
        },
        classification_choice_descriptor={
            "size_value": SimpleNamespace(name="size_value")
        },
        intervention={},
        unit={},
        findings_validator={
            "polyp_requires_lst_if_large": FindingsValidator.model_validate(
                {
                    "name": "polyp_requires_lst_if_large",
                    "finding": "colon_polyp",
                    "operator": "condition",
                    "query": {
                        "finding": "colon_polyp",
                        "operator": "condition",
                        "condition": {
                            "any": [
                                {
                                    "classification": "lesion_size_mm",
                                    "comparator": "gte",
                                    "value": 10,
                                }
                            ],
                            "then_requires": [{"classification": "lst"}],
                        },
                    },
                }
            )
        },
        classification_validator={},
        intervention_validator={},
        unit_validator={},
        examination_validator={},
    )

    graph = build_terminology_graph(kb)
    node_ids = {node.node_id for node in graph.nodes}
    edge_keys = {
        (edge.source_node_id, edge.target_node_id, edge.edge_type)
        for edge in graph.edges
    }

    assert "finding:colon_polyp" in node_ids
    assert "classification:lesion_size_mm" in node_ids
    assert "rule:findings_validator:polyp_requires_lst_if_large" in node_ids
    assert (
        "finding:colon_polyp",
        "classification:lesion_size_mm",
        "finding_to_classification",
    ) in edge_keys
    assert (
        "finding:colon_polyp",
        "rule:findings_validator:polyp_requires_lst_if_large",
        "finding_to_rule",
    ) in edge_keys
    assert (
        "rule:findings_validator:polyp_requires_lst_if_large",
        "classification:lesion_size_mm",
        "rule_condition",
    ) in edge_keys
    assert (
        "rule:findings_validator:polyp_requires_lst_if_large",
        "classification:lst",
        "rule_requires",
    ) in edge_keys

    mermaid = graph.export_mermaid()
    dot = graph.export_dot()

    assert "flowchart LR" in mermaid
    assert "polyp_requires_lst_if_large" in mermaid
    assert "digraph terminology_graph" in dot
