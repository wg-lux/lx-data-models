from __future__ import annotations

from types import SimpleNamespace

from lx_dtypes.models.knowledge_base.report_template.ReportFinding import ReportFinding
from lx_dtypes.models.knowledge_base.report_template.ReportTemplate import (
    ReportTemplate,
)
from lx_dtypes.models.knowledge_base.report_template.ReportTemplateGraph import (
    build_report_template_graph,
    validate_report_template_knowledge_base,
    validate_report_template_structure,
)
from lx_dtypes.models.knowledge_base.report_template.ReportTemplateSection import (
    ReportTemplateSection,
)


def _template() -> ReportTemplate:
    return ReportTemplate.model_validate(
        {
            "name": "demo_template",
            "examination": "demo_endoscopy",
            "report_sections": ["sec_a", "sec_b"],
            "validators": {
                "examination_validators": ["exam_validator_a"],
                "findings_validators": ["finding_validator_b"],
            },
        }
    )


def _sections() -> dict[str, ReportTemplateSection]:
    return {
        "sec_a": ReportTemplateSection.model_validate(
            {
                "name": "sec_a",
                "position": 0,
                "types": ["baseline"],
                "findings": [
                    "rf_polyp",
                    {
                        "finding": "bleeding_site",
                        "required": False,
                        "multiple_allowed": False,
                        "classifications": [
                            {"classification": "severity_grade", "required": True}
                        ],
                    },
                ],
            }
        ),
        "sec_b": ReportTemplateSection.model_validate(
            {
                "name": "sec_b",
                "position": 1,
                "types": ["follow_up"],
                "findings": [],
            }
        ),
    }


def _report_findings() -> dict[str, ReportFinding]:
    return {
        "rf_polyp": ReportFinding.model_validate(
            {
                "name": "rf_polyp",
                "finding": "esophagus_polyp",
                "required": True,
                "multiple_allowed": False,
                "classifications": [
                    {"classification": "size_mm", "required": True},
                    {"classification": "shape", "required": False},
                ],
            }
        )
    }


def test_build_report_template_graph_creates_expected_nodes_edges_and_weights() -> None:
    graph = build_report_template_graph(
        _template(),
        sections=_sections(),
        report_findings=_report_findings(),
    )

    assert graph.template_name == "demo_template"
    assert graph.start_node_id == "section:sec_a"
    assert graph.ordered_section_node_ids == ["section:sec_a", "section:sec_b"]

    nodes_by_id = {node.node_id: node for node in graph.nodes}
    assert "template:demo_template" in nodes_by_id
    assert "section:sec_a" in nodes_by_id
    assert "section:sec_b" in nodes_by_id
    assert "finding:esophagus_polyp" in nodes_by_id
    assert "finding:bleeding_site" in nodes_by_id
    assert "classification:size_mm" in nodes_by_id
    assert "classification:shape" in nodes_by_id
    assert "classification:severity_grade" in nodes_by_id
    assert "validator:exam_validator_a" in nodes_by_id
    assert "validator:finding_validator_b" in nodes_by_id

    edges = {(e.source_node_id, e.target_node_id, e.edge_type): e for e in graph.edges}
    assert ("template:demo_template", "section:sec_a", "template_to_section") in edges
    assert ("template:demo_template", "section:sec_b", "template_to_section") in edges
    assert ("section:sec_a", "section:sec_b", "section_sequence") in edges
    assert ("section:sec_a", "finding:esophagus_polyp", "section_to_finding") in edges
    assert ("section:sec_a", "finding:bleeding_site", "section_to_finding") in edges
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

    # sec_a has 2 findings -> normalized edge weight 0.5 each
    assert (
        edges[("section:sec_a", "finding:esophagus_polyp", "section_to_finding")].weight
        == 0.5
    )
    # rf_polyp has 2 classifications -> normalized edge weight 0.5
    assert (
        edges[
            (
                "finding:esophagus_polyp",
                "classification:size_mm",
                "finding_to_classification",
            )
        ].weight
        == 0.5
    )
    # validator edges currently fixed
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


def test_validate_report_template_structure_reports_warnings_and_errors() -> None:
    template = ReportTemplate.model_validate(
        {
            "name": "broken_template",
            "examination": "demo_endoscopy",
            "report_sections": ["missing_section", "sec_a", "sec_a"],
            "validators": {"examination_validators": [], "findings_validators": []},
        }
    )
    sections = {
        "sec_a": ReportTemplateSection.model_validate(
            {"name": "sec_a", "position": 0, "types": [], "findings": ["unknown_alias"]}
        )
    }

    result = validate_report_template_structure(
        template,
        sections=sections,
        report_findings={},
        findings={},
    )

    assert result.ok is False
    codes = [issue.code for issue in result.issues]
    assert "missing_section" in codes
    assert "duplicate_section_reference" in codes
    assert "unknown_finding_reference" in codes


def test_validate_report_template_knowledge_base_returns_per_template_results() -> None:
    valid_template = ReportTemplate.model_validate(
        {
            "name": "valid_t",
            "examination": "demo_endoscopy",
            "report_sections": ["sec_a"],
            "validators": {"examination_validators": [], "findings_validators": []},
        }
    )
    invalid_template = ReportTemplate.model_validate(
        {
            "name": "invalid_t",
            "examination": "demo_endoscopy",
            "report_sections": ["missing_sec"],
            "validators": {"examination_validators": [], "findings_validators": []},
        }
    )
    kb = SimpleNamespace(
        report_template={"valid_t": valid_template, "invalid_t": invalid_template},
        report_template_section={
            "sec_a": ReportTemplateSection.model_validate(
                {
                    "name": "sec_a",
                    "position": 0,
                    "types": [],
                    "findings": [
                        {
                            "finding": "f1",
                            "required": False,
                            "multiple_allowed": False,
                            "classifications": [],
                        }
                    ],
                }
            )
        },
        report_finding={},
        finding={"f1": {"name": "f1"}},
    )

    results = validate_report_template_knowledge_base(kb)
    assert set(results.keys()) == {"valid_t", "invalid_t"}
    assert results["valid_t"].ok is True
    assert results["invalid_t"].ok is False


def test_graph_and_validation_result_as_ddict_are_serializable_shapes() -> None:
    result = validate_report_template_structure(
        ReportTemplate.model_validate(
            {
                "name": "t",
                "examination": "e",
                "report_sections": [],
                "validators": {"examination_validators": [], "findings_validators": []},
            }
        ),
        sections={},
        report_findings={},
        findings={},
    )
    result_ddict = result.as_ddict()
    assert result_ddict["template_name"] == "t"
    assert "graph" in result_ddict
    assert isinstance(result_ddict["issues"], list)


def test_build_report_template_graph_includes_patient_and_history_field_nodes() -> None:
    template = ReportTemplate.model_validate(
        {
            "name": "t_fields",
            "examination": "demo_endoscopy",
            "report_sections": ["patient_sec", "history_sec"],
            "validators": {"examination_validators": [], "findings_validators": []},
        }
    )
    sections = {
        "patient_sec": ReportTemplateSection.model_validate(
            {
                "name": "patient_sec",
                "position": 0,
                "types": ["patient_data"],
                "section_kind": "patient_data",
                "fields": [
                    {"key": "patient_birth_date", "source": "patient"},
                    {"key": "indication", "source": "patient_examination"},
                ],
                "findings": [],
            }
        ),
        "history_sec": ReportTemplateSection.model_validate(
            {
                "name": "history_sec",
                "position": 1,
                "types": ["history"],
                "section_kind": "history",
                "fields": [{"key": "previous_examinations", "source": "history"}],
                "findings": [],
            }
        ),
    }

    graph = build_report_template_graph(template, sections=sections, report_findings={})
    nodes_by_id = {node.node_id: node for node in graph.nodes}
    edges = {(e.source_node_id, e.target_node_id, e.edge_type): e for e in graph.edges}

    assert nodes_by_id["patient_field:patient_birth_date"].node_type == "patient_field"
    assert nodes_by_id["patient_field:indication"].node_type == "patient_field"
    assert (
        nodes_by_id["history_field:previous_examinations"].node_type == "history_field"
    )
    assert (
        "section:patient_sec",
        "patient_field:patient_birth_date",
        "section_to_patient_field",
    ) in edges
    assert (
        "section:history_sec",
        "history_field:previous_examinations",
        "section_to_history_field",
    ) in edges
    assert (
        edges[
            (
                "section:patient_sec",
                "patient_field:patient_birth_date",
                "section_to_patient_field",
            )
        ].weight
        == 0.5
    )


def test_validate_report_template_structure_validates_non_finding_sections() -> None:
    template = ReportTemplate.model_validate(
        {
            "name": "patient_template",
            "examination": "demo_endoscopy",
            "report_sections": ["patient_sec", "history_sec"],
            "validators": {"examination_validators": [], "findings_validators": []},
        }
    )
    sections = {
        "patient_sec": ReportTemplateSection.model_validate(
            {
                "name": "patient_sec",
                "position": 0,
                "types": ["patient_data"],
                "section_kind": "patient_data",
                "fields": [
                    {"key": "patient_birth_date", "source": "patient"},
                    {"key": "patient_birth_date", "source": "patient"},
                    {"key": "previous_examinations", "source": "history"},
                    {"key": "unknown_field_key"},
                ],
                "findings": ["unknown_alias"],
            }
        ),
        "history_sec": ReportTemplateSection.model_validate(
            {
                "name": "history_sec",
                "position": 1,
                "types": ["history"],
                "section_kind": "history",
                "fields": [{"key": "previous_examinations", "source": "patient"}],
                "findings": [],
            }
        ),
    }

    result = validate_report_template_structure(
        template,
        sections=sections,
        report_findings={},
        findings={},
    )

    codes = [issue.code for issue in result.issues]
    assert "non_finding_section_has_findings" in codes
    assert "duplicate_section_field" in codes
    assert "section_field_kind_mismatch" in codes
    assert "unknown_section_field_key" in codes
    assert "section_field_source_mismatch" in codes
    assert "unknown_finding_reference" not in codes
