from __future__ import annotations

from lx_dtypes.models.knowledge_base.report_template.PropertyGraph import (
    PropertyGraph,
    PropertyGraphEdge,
    PropertyGraphNode,
)
from lx_dtypes.models.knowledge_base.report_template.ReportFinding import ReportFinding
from lx_dtypes.models.knowledge_base.report_template.ReportTemplate import (
    ReportTemplate,
)
from lx_dtypes.models.knowledge_base.report_template.ReportTemplateGraph import (
    ReportTemplatePropertyGraphAdapter,
)
from lx_dtypes.models.knowledge_base.report_template.ReportTemplateSection import (
    ReportTemplateSection,
)


def test_property_graph_core_supports_generic_nodes_and_edges() -> None:
    graph = PropertyGraph(
        nodes={
            "root": PropertyGraphNode(
                id="root",
                kind="root_kind",
                labels=["Root"],
                metadata={"name": "Root"},
            )
        },
        edges=[
            PropertyGraphEdge(
                source="root",
                target="child",
                kind="contains",
                weight=2.5,
                properties={"rank": 1},
            )
        ],
    )

    assert graph.nodes["root"].kind == "root_kind"
    assert graph.edges[0].kind == "contains"
    assert graph.edges[0].properties["rank"] == 1


def test_report_template_property_graph_adapter_projects_domain_semantics() -> None:
    template = ReportTemplate.model_validate(
        {
            "name": "demo_template",
            "examination": "demo_endoscopy",
            "report_sections": ["sec_a"],
            "validators": {
                "examination_validators": ["exam_validator_a"],
                "findings_validators": [],
            },
        }
    )
    sections = {
        "sec_a": ReportTemplateSection.model_validate(
            {
                "name": "sec_a",
                "position": 0,
                "types": ["baseline"],
                "findings": ["rf_polyp"],
            }
        )
    }
    report_findings = {
        "rf_polyp": ReportFinding.model_validate(
            {
                "name": "rf_polyp",
                "finding": "esophagus_polyp",
                "required": True,
                "multiple_allowed": False,
                "classifications": [
                    {"classification": "size_mm", "required": True}
                ],
            }
        )
    }

    graph = ReportTemplatePropertyGraphAdapter().build(
        template,
        sections=sections,
        report_findings=report_findings,
    )

    assert graph.nodes["template:demo_template"].kind == "template"
    assert graph.nodes["template:demo_template"].metadata["examination"] == (
        "demo_endoscopy"
    )
    assert graph.nodes["section:sec_a"].kind == "section"
    assert graph.nodes["finding:esophagus_polyp"].kind == "finding"
    assert graph.nodes["classification:size_mm"].kind == "classification"
    assert graph.nodes["validator:exam_validator_a"].kind == "validator"

    edges = {(edge.source, edge.target, edge.kind): edge for edge in graph.edges}
    assert ("template:demo_template", "section:sec_a", "template_to_section") in edges
    assert ("section:sec_a", "finding:esophagus_polyp", "section_to_finding") in edges
    assert (
        "finding:esophagus_polyp",
        "classification:size_mm",
        "finding_to_classification",
    ) in edges
    assert (
        "template:demo_template",
        "validator:exam_validator_a",
        "template_to_validator",
    ) in edges
    assert (
        edges[
            (
                "template:demo_template",
                "validator:exam_validator_a",
                "template_to_validator",
            )
        ].weight
        == 0.4
    )
