from __future__ import annotations

from pathlib import Path

from lx_dtypes.utils.kb_yaml_lint import (
    discover_yaml_files,
    lint_kb_yaml_files,
)
from lx_dtypes.utils.parser import parse_shallow_object_with_meta


def test_parse_with_meta_tracks_item_line_numbers(tmp_path: Path) -> None:
    data_file = tmp_path / "concepts.yaml"
    data_file.write_text(
        (
            "- model: finding\n"
            "  name: finding_a\n"
            "- model: finding_type\n"
            "  name: finding_type_a\n"
        ),
        encoding="utf-8",
    )

    parsed = parse_shallow_object_with_meta(data_file, kb_module_name="demo")
    assert len(parsed) == 2
    assert parsed[0].line == 1
    assert parsed[1].line == 3
    assert parsed[0].parsed_object.name == "finding_a"


def test_linter_reports_duplicate_name_with_line_reference(tmp_path: Path) -> None:
    data_file = tmp_path / "duplicates.yaml"
    data_file.write_text(
        (
            "- model: finding\n"
            "  name: duplicated_finding\n"
            "- model: finding\n"
            "  name: duplicated_finding\n"
        ),
        encoding="utf-8",
    )

    issues = lint_kb_yaml_files([data_file])
    duplicate_issues = [issue for issue in issues if issue.code == "duplicate_name"]
    assert len(duplicate_issues) == 1
    issue = duplicate_issues[0]
    assert issue.line == 3
    assert issue.column == 3
    assert "previously defined at" in issue.message


def test_linter_flags_alias_and_mixed_style(tmp_path: Path) -> None:
    data_file = tmp_path / "report_templates.yaml"
    data_file.write_text(
        (
            "- model: finding_validator\n"
            "  name: alias_validator\n"
            "  finding: finding_a\n"
            "  operator: exists\n"
            "  query:\n"
            "    finding: finding_a\n"
            "    operator: exists\n"
            "- model: report_template_section\n"
            "  name: section_a\n"
            "  findings:\n"
            "    - finding_a\n"
            "    - finding: finding_b\n"
            "      required: false\n"
            "      multiple_allowed: false\n"
            "      classifications: []\n"
        ),
        encoding="utf-8",
    )

    issues = lint_kb_yaml_files([data_file])
    codes = {issue.code for issue in issues}
    assert "alias_model_name" in codes
    assert "mixed_finding_reference_styles" in codes

    strict_alias_issues = lint_kb_yaml_files([data_file], strict_aliases=True)
    alias_issue = next(issue for issue in strict_alias_issues if issue.code == "alias_model_name")
    assert alias_issue.severity == "error"


def test_discover_yaml_files_expands_module_config(tmp_path: Path) -> None:
    module_dir = tmp_path / "module"
    data_dir = module_dir / "data"
    module_dir.mkdir()
    data_dir.mkdir()

    config_file = module_dir / "config.yaml"
    config_file.write_text(
        (
            "name: demo_module\n"
            "version: \"1.0.0\"\n"
            "data:\n"
            "  files:\n"
            "    - data/findings.yaml\n"
        ),
        encoding="utf-8",
    )

    target_file = data_dir / "findings.yaml"
    target_file.write_text("- model: finding\n  name: finding_a\n", encoding="utf-8")

    files, issues = discover_yaml_files(paths=[], config_paths=[config_file])
    assert issues == []
    assert files == [target_file.resolve()]
