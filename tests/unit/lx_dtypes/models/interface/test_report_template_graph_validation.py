from __future__ import annotations

from pathlib import Path

import yaml

from lx_dtypes.models.interface.DataLoader import DataLoader
from lx_dtypes.models.knowledge_base.report_template import (
    validate_report_template_knowledge_base,
    validate_report_template_structure,
)


def test_report_template_structure_validation_from_examples() -> None:
    loader = DataLoader(input_dirs=[Path("./lx_dtypes/data/")])
    loader.load_module_configs()
    kb = loader.load_knowledge_base("report_template_examples")

    template = kb.get_report_template("star_upper_gi_main")
    result = validate_report_template_structure(
        template,
        sections=kb.report_template_section,
        report_findings=kb.report_finding,
        findings=kb.finding,
    )

    assert result.graph.template_name == "star_upper_gi_main"
    assert result.graph.start_node_id.startswith("section:")
    assert all(issue.level != "error" for issue in result.issues)

    base_template = kb.get_report_template("base_report_template")
    base_result = validate_report_template_structure(
        base_template,
        sections=kb.report_template_section,
        report_findings=kb.report_finding,
        findings=kb.finding,
    )
    assert base_result.ok is True
    assert base_result.graph.template_name == "base_report_template"
    assert base_result.graph.ordered_section_node_ids == [
        "section:base_required_section"
    ]


def test_report_template_structure_validation_finds_missing_section(
    tmp_path: Path,
) -> None:
    module_dir = tmp_path / "rt_graph_module"
    module_dir.mkdir(parents=True)

    config_path = module_dir / "config.yaml"
    data_path = module_dir / "report_template.yaml"

    config_path.write_text(
        yaml.safe_dump(
            {
                "name": "rt_graph_module",
                "version": "1.0.0",
                "modules": [],
                "depends_on": [],
                "data": {"files": ["./report_template.yaml"]},
            }
        ),
        encoding="utf-8",
    )

    data_path.write_text(
        yaml.safe_dump(
            [
                {
                    "model": "report_template",
                    "name": "broken_template",
                    "examination": "colonoscopy",
                    "report_sections": ["missing_section"],
                    "validators": {
                        "examination_validators": [],
                        "findings_validators": [],
                    },
                }
            ],
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    loader = DataLoader(input_dirs=[tmp_path])
    loader.load_module_configs()
    kb = loader.load_knowledge_base("rt_graph_module")

    summary = validate_report_template_knowledge_base(kb)
    result = summary["broken_template"]
    assert result.ok is False
    assert any(issue.code == "missing_section" for issue in result.issues)
