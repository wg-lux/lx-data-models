from __future__ import annotations

from typing import Any

import pytest

from lx_dtypes.models.knowledge_base.report_template import (
    ReportFinding,
    ReportTemplate,
    ReportTemplateSection,
    validate_report_template_structure,
)


@pytest.fixture(params=["kb_alias", "inline"])
def template_with_findings(
    request: pytest.FixtureRequest,
) -> tuple[
    ReportTemplate,
    dict[str, ReportTemplateSection],
    dict[str, ReportFinding],
    dict[str, Any],
]:
    mode = request.param

    template = ReportTemplate.model_validate(
        {
            "name": "test_template",
            "examination": "star_upper_gi_endoscopy",
            "report_sections": ["baseline"],
            "validators": {
                "examination_validators": [],
                "findings_validators": [],
            },
        }
    )

    report_findings: dict[str, ReportFinding] = {}
    if mode == "kb_alias":
        report_findings["rf_polyp"] = ReportFinding.model_validate(
            {
                "name": "rf_polyp",
                "finding": "esophagus_polyp",
                "required": True,
                "multiple_allowed": False,
                "classifications": [],
            }
        )
        section_findings: list[Any] = ["rf_polyp"]
    else:
        section_findings = [
            {
                "finding": "esophagus_polyp",
                "required": True,
                "multiple_allowed": False,
                "classifications": [],
            }
        ]

    sections = {
        "baseline": ReportTemplateSection.model_validate(
            {
                "name": "baseline",
                "position": 0,
                "types": ["baseline"],
                "findings": section_findings,
            }
        )
    }

    findings = {
        "esophagus_polyp": {
            "name": "esophagus_polyp",
        }
    }
    return template, sections, report_findings, findings


def test_kb_alias_and_inline_findings_resolve_to_same_graph_shape(
    template_with_findings: tuple[
        ReportTemplate,
        dict[str, ReportTemplateSection],
        dict[str, ReportFinding],
        dict[str, Any],
    ],
) -> None:
    template, sections, report_findings, findings = template_with_findings

    result = validate_report_template_structure(
        template,
        sections=sections,
        report_findings=report_findings,
        findings=findings,
    )

    assert result.ok is True
    assert not [issue for issue in result.issues if issue.level == "error"]

    graph = result.graph
    finding_nodes = [node for node in graph.nodes if node.node_type == "finding"]
    section_nodes = [node for node in graph.nodes if node.node_type == "section"]

    assert len(section_nodes) == 1
    assert section_nodes[0].name == "baseline"
    assert len(finding_nodes) == 1
    assert finding_nodes[0].name == "esophagus_polyp"

    edge_pairs = {(edge.source_node_id, edge.target_node_id) for edge in graph.edges}
    assert ("template:test_template", "section:baseline") in edge_pairs
    assert ("section:baseline", "finding:esophagus_polyp") in edge_pairs


def test_broken_alias_reference_surfaces_structure_problem() -> None:
    template = ReportTemplate.model_validate(
        {
            "name": "broken_alias_template",
            "examination": "star_upper_gi_endoscopy",
            "report_sections": ["baseline"],
            "validators": {
                "examination_validators": [],
                "findings_validators": [],
            },
        }
    )
    sections = {
        "baseline": ReportTemplateSection.model_validate(
            {
                "name": "baseline",
                "position": 0,
                "types": [],
                "findings": ["missing_rf_alias"],
            }
        )
    }

    result = validate_report_template_structure(
        template,
        sections=sections,
        report_findings={},
        findings={"esophagus_polyp": {"name": "esophagus_polyp"}},
    )

    # Alias is interpreted as a fallback finding name if no report_finding exists.
    # This should not be a hard parse failure, but we do want visibility.
    assert result.ok is True
    assert any(issue.code == "unknown_finding_reference" for issue in result.issues)


def test_inline_finding_without_kb_entry_surfaces_warning() -> None:
    template = ReportTemplate.model_validate(
        {
            "name": "inline_missing_kb",
            "examination": "star_upper_gi_endoscopy",
            "report_sections": ["baseline"],
            "validators": {
                "examination_validators": [],
                "findings_validators": [],
            },
        }
    )
    sections = {
        "baseline": ReportTemplateSection.model_validate(
            {
                "name": "baseline",
                "position": 0,
                "types": [],
                "findings": [
                    {
                        "finding": "non_existing_finding",
                        "required": True,
                        "multiple_allowed": False,
                        "classifications": [],
                    }
                ],
            }
        )
    }

    result = validate_report_template_structure(
        template,
        sections=sections,
        report_findings={},
        findings={},
    )

    assert result.ok is True
    assert any(issue.code == "unknown_finding_reference" for issue in result.issues)
