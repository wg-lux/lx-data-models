from pathlib import Path

import pytest
import yaml

from lx_dtypes.models.interface.DataLoader import DataLoader


def _write_module(
    tmp_path: Path,
    *,
    lifecycle_status: str,
    records: list[dict[str, int | str | dict[str, list[str]] | list[str]]],
) -> None:
    module_dir = tmp_path / "report_module"
    generated_dir = module_dir / "generated_templates"
    generated_dir.mkdir(parents=True)

    (module_dir / "config.yaml").write_text(
        yaml.safe_dump(
            {
                "name": "report_module",
                "version": "1.0.0",
                "modules": [],
                "depends_on": [],
                "data": {
                    "dirs": ["./generated_templates"],
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    (generated_dir / "template.yaml").write_text(
        yaml.safe_dump(records, sort_keys=False),
        encoding="utf-8",
    )
    (generated_dir / "report_template_registry.yaml").write_text(
        yaml.safe_dump(
            {
                "templates": {
                    "custom_template": {"lifecycle_status": lifecycle_status},
                }
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def test_report_template_preview_keeps_draft_and_issues(tmp_path: Path) -> None:
    _write_module(
        tmp_path,
        lifecycle_status="draft",
        records=[
            {
                "model": "finding",
                "name": "esophagus_polyp",
                "classifications": [],
            },
            {
                "model": "examination",
                "name": "star_upper_gi_endoscopy",
                "findings": ["esophagus_polyp"],
            },
            {
                "model": "report_template_section",
                "name": "baseline",
                "position": 0,
                "findings": ["esophagus_polyp"],
            },
            {
                "model": "report_template",
                "name": "custom_template",
                "examination": "star_upper_gi_endoscopy",
                "report_sections": ["baseline"],
                "validators": {
                    "findings_validators": ["missing_validator"],
                    "examination_validators": [],
                },
            },
        ],
    )
    loader = DataLoader(input_dirs=[tmp_path])
    loader.load_module_configs()
    kb = loader.load_knowledge_base("report_module")

    preview = kb.export_report_template_preview("custom_template")

    assert preview["lifecycle_status"] == "draft"
    assert preview["readiness"]["can_preview"] is True
    assert preview["readiness"]["can_publish"] is False
    assert any(
        issue["code"] == "unknown_findings_validator_reference"
        for issue in preview["issues"]
    )
    with pytest.raises(KeyError):
        kb.export_report_template("custom_template")


def test_report_template_production_export_requires_published_status(
    tmp_path: Path,
) -> None:
    _write_module(
        tmp_path,
        lifecycle_status="draft",
        records=[
            {
                "model": "finding",
                "name": "esophagus_polyp",
                "classifications": [],
            },
            {
                "model": "examination",
                "name": "star_upper_gi_endoscopy",
                "findings": ["esophagus_polyp"],
            },
            {
                "model": "report_template_section",
                "name": "baseline",
                "position": 0,
                "findings": ["esophagus_polyp"],
            },
            {
                "model": "report_template",
                "name": "custom_template",
                "examination": "star_upper_gi_endoscopy",
                "report_sections": ["baseline"],
                "validators": {
                    "findings_validators": [],
                    "examination_validators": [],
                },
            },
        ],
    )
    loader = DataLoader(input_dirs=[tmp_path])
    loader.load_module_configs()
    kb = loader.load_knowledge_base("report_module")

    with pytest.raises(KeyError):
        kb.export_report_template("custom_template")

    kb.report_template_lifecycle_status["custom_template"] = "published"
    exported = kb.export_report_template("custom_template")
    assert exported["name"] == "custom_template"
    assert exported["lifecycle_status"] == "published"
