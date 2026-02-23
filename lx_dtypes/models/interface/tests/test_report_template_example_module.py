import json
from pathlib import Path

import pytest
import yaml

from lx_dtypes.models.interface.DataLoader import DataLoader
from lx_dtypes.models.knowledge_base.report_template.ReportTemplate import ReportTemplate
from lx_dtypes.models.knowledge_base.report_template.ReportTemplateGraph import (
    validate_report_template_structure,
)


def test_report_template_example_module_yaml_json_roundtrip() -> None:
    loader = DataLoader(input_dirs=[Path("./lx_dtypes/data/")])
    loader.load_module_configs()
    kb = loader.load_knowledge_base("report_template_examples")

    exported = kb.export_report_template("star_upper_gi_main")

    exported_json = json.dumps(exported, sort_keys=True, default=str)
    exported_back = json.loads(exported_json)

    assert exported_back["name"] == "star_upper_gi_main"
    assert exported_back["examination"] == "star_upper_gi_endoscopy"
    assert len(exported_back["report_sections"]) == 2

    template = kb.get_report_template("star_upper_gi_main")
    template_json = template.model_dump_json()
    template_back = ReportTemplate.model_validate_json(template_json)

    assert template_back.model_dump() == template.model_dump()

    assert exported_back["validators"]["findings_validators"][0]["name"] == (
        "polyp_has_lst_if_large"
    )
    assert exported_back["validators"]["examination_validators"][0]["name"] == (
        "gastroscopy_has_baseline_info"
    )


@pytest.fixture(params=["kb_alias", "inline"])
def report_template_module(tmp_path: Path, request: pytest.FixtureRequest) -> Path:
    mode = request.param
    module_dir = tmp_path / f"rt_{mode}"
    module_dir.mkdir(parents=True)

    (module_dir / "config.yaml").write_text(
        yaml.safe_dump(
            {
                "name": f"rt_{mode}",
                "version": "1.0.0",
                "modules": [],
                "depends_on": [],
                "data": {"files": ["./report_template.yaml"]},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    records = [
        {"model": "finding", "name": "esophagus_polyp"},
        {
            "model": "examination",
            "name": "star_upper_gi_endoscopy",
            "findings": ["esophagus_polyp"],
        },
    ]

    if mode == "kb_alias":
        records.append(
            {
                "model": "report_finding",
                "name": "rf_polyp",
                "finding": "esophagus_polyp",
                "required": True,
                "multiple_allowed": False,
                "classifications": [],
            }
        )
        section_findings = ["rf_polyp"]
    else:
        section_findings = [
            {
                "finding": "esophagus_polyp",
                "required": True,
                "multiple_allowed": False,
                "classifications": [],
            }
        ]

    records.extend(
        [
            {
                "model": "report_template_section",
                "name": "baseline",
                "position": 0,
                "types": ["baseline"],
                "findings": section_findings,
            },
            {
                "model": "report_template",
                "name": "test_template",
                "examination": "star_upper_gi_endoscopy",
                "report_sections": ["baseline"],
                "validators": {
                    "examination_validators": [],
                    "findings_validators": [],
                },
            },
        ]
    )

    (module_dir / "report_template.yaml").write_text(
        yaml.safe_dump(records, sort_keys=False),
        encoding="utf-8",
    )
    return module_dir


def test_report_template_validator_inline_vs_kb_alias_parity(
    report_template_module: Path,
) -> None:
    loader = DataLoader(input_dirs=[report_template_module.parent])
    loader.load_module_configs()
    kb = loader.load_knowledge_base(report_template_module.name)

    template = kb.get_report_template("test_template")
    result = validate_report_template_structure(
        template,
        sections=kb.report_template_section,
        report_findings=kb.report_finding,
        findings=kb.finding,
    )

    assert result.ok is True
    assert not [issue for issue in result.issues if issue.level == "error"]

    graph = result.graph
    finding_nodes = [n for n in graph.nodes if n.node_type == "finding"]
    section_nodes = [n for n in graph.nodes if n.node_type == "section"]

    assert len(section_nodes) == 1
    assert section_nodes[0].name == "baseline"
    assert len(finding_nodes) == 1
    assert finding_nodes[0].name == "esophagus_polyp"


def test_report_template_validator_broken_alias_surfaces_warning(tmp_path: Path) -> None:
    module_dir = tmp_path / "rt_broken_alias"
    module_dir.mkdir(parents=True)
    (module_dir / "config.yaml").write_text(
        yaml.safe_dump(
            {
                "name": "rt_broken_alias",
                "version": "1.0.0",
                "modules": [],
                "depends_on": [],
                "data": {"files": ["./report_template.yaml"]},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    (module_dir / "report_template.yaml").write_text(
        yaml.safe_dump(
            [
                {"model": "finding", "name": "esophagus_polyp"},
                {
                    "model": "examination",
                    "name": "star_upper_gi_endoscopy",
                    "findings": ["esophagus_polyp"],
                },
                {
                    "model": "report_template_section",
                    "name": "baseline",
                    "position": 0,
                    "types": [],
                    "findings": ["missing_rf_alias"],
                },
                {
                    "model": "report_template",
                    "name": "test_template",
                    "examination": "star_upper_gi_endoscopy",
                    "report_sections": ["baseline"],
                    "validators": {
                        "examination_validators": [],
                        "findings_validators": [],
                    },
                },
            ],
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    loader = DataLoader(input_dirs=[module_dir.parent])
    loader.load_module_configs()
    kb = loader.load_knowledge_base(module_dir.name)
    template = kb.get_report_template("test_template")
    result = validate_report_template_structure(
        template,
        sections=kb.report_template_section,
        report_findings=kb.report_finding,
        findings=kb.finding,
    )

    assert result.ok is True
    assert any(issue.code == "unknown_finding_reference" for issue in result.issues)
