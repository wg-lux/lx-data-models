from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from lx_dtypes.scripts.lint_kb_yaml import parse_args
from lx_dtypes.utils.kb_yaml_lint import (
    discover_yaml_files,
    lint_kb_yaml_files,
)
from lx_dtypes.utils.parser import parse_shallow_object_with_meta


def test_guideline_extension_files_declare_sources() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    terminology_root = repository_root / "lx_dtypes/data/terminology"
    sourced_files = [
        terminology_root / "lx_units/data/canonical_medication.yaml",
        terminology_root / "lx_units/data/sedation_documentation.yaml",
        terminology_root / "lx_descriptors/data/colonoscopy.yaml",
        terminology_root / "lx_descriptors/data/medication.yaml",
        terminology_root / "lx_descriptors/data/sedation_documentation.yaml",
        terminology_root / "lx_descriptors/data/endoscopy_process_timing.yaml",
        terminology_root / "lx_descriptors/data/endoscopy_team_timeout.yaml",
        terminology_root / "lx_descriptors/data/endoscopy_risk_assessment.yaml",
    ]
    for family in (
        "lx_classification_choices",
        "lx_classifications",
        "lx_findings",
    ):
        sourced_files.extend(
            terminology_root / family / "data" / f"00_generic_{topic}.yaml"
            for topic in (
                "medication",
                "sedation_documentation",
                "endoscopy_process_timing",
                "endoscopy_team_timeout",
                "endoscopy_risk_assessment",
            )
        )

    for source_file in sourced_files:
        header = "\n".join(source_file.read_text(encoding="utf-8").splitlines()[:6])
        assert "Sources for every record in this file:" in header, source_file
        assert "https://" in header, source_file

    shared_files = [
        terminology_root / relative_path
        for relative_path in (
            "lx_classification_choices/data/00_generic.yaml",
            "lx_classification_choices/data/00_generic_baseline.yaml",
            "lx_classification_choices/data/00_generic_complication.yaml",
            "lx_classification_choices/data/00_generic_lesion.yaml",
            "lx_classification_choices/data/02_colonoscopy_bowel_preparation.yaml",
            "lx_classification_choices/data/02_colonoscopy_generic.yaml",
            "lx_classification_choices/data/02_colonoscopy_location.yaml",
            "lx_classification_choices/data/02_colonoscopy_other.yaml",
            "lx_classification_choices/data/02_colonoscopy_polyp_advanced_imaging.yaml",
            "lx_classification_choices/data/02_colonoscopy_polyp_morphology.yaml",
            "lx_classifications/data/00_generic.yaml",
            "lx_classifications/data/02_colonoscopy_baseline.yaml",
            "lx_classifications/data/02_colonoscopy_other.yaml",
            "lx_descriptors/data/time.yaml",
            "lx_findings/data/00_generic.yaml",
            "lx_findings/data/00_generic_complication.yaml",
            "lx_findings/data/02_colonoscopy_baseline.yaml",
            "lx_findings/data/02_colonoscopy_observation.yaml",
            "lx_units/data/misc.yaml",
        )
    ]
    for source_file in shared_files:
        header = "\n".join(source_file.read_text(encoding="utf-8").splitlines()[:6])
        assert "Sources for guideline-derived additions in this file:" in header
        assert "https://" in header, source_file

    for integration_file in (
        repository_root
        / "lx_dtypes/data/terminology/lx_examinations/data/colonoscopy.yaml",
        repository_root
        / "lx_dtypes/data/report_template_examples/report_templates.yaml",
    ):
        content = integration_file.read_text(encoding="utf-8")
        assert "DGVS S2k quality guideline" in content, integration_file
        assert "DGVS S3 sedation guideline" in content, integration_file


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


def test_linter_rejects_duplicate_yaml_mapping_key(tmp_path: Path) -> None:
    data_file = tmp_path / "duplicate_key.yaml"
    data_file.write_text(
        (
            "- model: finding\n"
            "  name: complication_generic\n"
            "  name_de: Komplikation\n"
            "  name_de: Komplikation (generisch)\n"
        ),
        encoding="utf-8",
    )

    issues = lint_kb_yaml_files([data_file])

    issue = next(issue for issue in issues if issue.code == "duplicate_mapping_key")
    assert issue.severity == "error"
    assert issue.line == 4
    assert issue.column == 3
    assert "name_de" in issue.message
    assert ":3:3" in issue.message


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
    alias_issue = next(
        issue for issue in strict_alias_issues if issue.code == "alias_model_name"
    )
    assert alias_issue.severity == "error"


def test_linter_flags_descriptor_backed_coverage_without_value_path(
    tmp_path: Path,
) -> None:
    data_file = tmp_path / "descriptor_rule.yaml"
    data_file.write_text(
        (
            "- model: classification_choice_descriptor\n"
            "  name: minutes_value\n"
            "  classification_choice_descriptor_type: numeric\n"
            "- model: classification_choice\n"
            "  name: minutes_choice\n"
            "  classification_choice_descriptors:\n"
            "    - minutes_value\n"
            "- model: classification\n"
            "  name: time_minutes\n"
            "  classification_choices:\n"
            "    - minutes_choice\n"
            "- model: report_template\n"
            "  name: colonoscopy_report\n"
            "  examination: colonoscopy\n"
            "  coverage_concepts:\n"
            "    - concept_id: colonoscopy.withdrawal_time\n"
            "      label: Withdrawal time\n"
            "      applicability_status: required\n"
            "      validator_names:\n"
            "        - withdrawal_time_recorded\n"
            "      evidence_path:\n"
            "        - patient_findings\n"
            "      finding_selector:\n"
            "        finding_name: withdrawal_time\n"
            "        classification_name: time_minutes\n"
            "      allowed_values:\n"
            "        - minutes_choice\n"
        ),
        encoding="utf-8",
    )

    issues = lint_kb_yaml_files([data_file])
    issue = next(
        issue for issue in issues if issue.code == "incomplete_descriptor_value_rule"
    )
    assert issue.severity == "warning"
    assert "minutes_value" in issue.message
    assert "descriptor_value" in issue.message


def test_linter_accepts_coverage_that_targets_descriptor_value(tmp_path: Path) -> None:
    data_file = tmp_path / "complete_descriptor_rule.yaml"
    data_file.write_text(
        (
            "- model: classification_choice_descriptor\n"
            "  name: minutes_value\n"
            "  classification_choice_descriptor_type: numeric\n"
            "- model: classification_choice\n"
            "  name: minutes_choice\n"
            "  classification_choice_descriptors:\n"
            "    - minutes_value\n"
            "- model: classification\n"
            "  name: time_minutes\n"
            "  classification_choices:\n"
            "    - minutes_choice\n"
            "- model: report_template\n"
            "  name: colonoscopy_report\n"
            "  examination: colonoscopy\n"
            "  coverage_concepts:\n"
            "    - concept_id: colonoscopy.withdrawal_time\n"
            "      label: Withdrawal time\n"
            "      applicability_status: required\n"
            "      validator_names:\n"
            "        - withdrawal_time_recorded\n"
            "      evidence_path:\n"
            "        - patient_findings\n"
            "      concept_value_path:\n"
            "        - patient_finding_classification_choice_descriptors\n"
            '        - "0"\n'
            "        - descriptor_value\n"
            "      finding_selector:\n"
            "        finding_name: withdrawal_time\n"
            "        classification_name: time_minutes\n"
            "      allowed_values:\n"
            "        - 6\n"
        ),
        encoding="utf-8",
    )

    issues = lint_kb_yaml_files([data_file])
    assert not any(issue.code == "incomplete_descriptor_value_rule" for issue in issues)


def test_linter_flags_broken_classification_input_chain(tmp_path: Path) -> None:
    data_file = tmp_path / "broken_input_chain.yaml"
    data_file.write_text(
        (
            "- model: classification\n"
            "  name: empty_classification\n"
            "  classification_choices: []\n"
            "- model: classification\n"
            "  name: missing_choice_classification\n"
            "  classification_choices:\n"
            "    - missing_choice\n"
            "- model: classification_choice\n"
            "  name: broken_descriptor_choice\n"
            "  classification_choice_descriptors:\n"
            "    - missing_descriptor\n"
            "- model: classification\n"
            "  name: broken_descriptor_classification\n"
            "  classification_choices:\n"
            "    - broken_descriptor_choice\n"
        ),
        encoding="utf-8",
    )

    issues = lint_kb_yaml_files([data_file])
    codes = {issue.code for issue in issues}
    assert "classification_has_no_enterable_values" in codes
    assert "missing_classification_choice_reference" in codes
    assert "missing_choice_descriptor_reference" in codes


def test_linter_rejects_descriptor_with_unresolved_unit(tmp_path: Path) -> None:
    data_file = tmp_path / "unresolved_unit.yaml"
    data_file.write_text(
        (
            "- model: classification_choice_descriptor\n"
            "  name: mst30_count_value\n"
            "  classification_choice_descriptor_type: numeric\n"
            "  unit: unknown\n"
        ),
        encoding="utf-8",
    )

    issues = lint_kb_yaml_files([data_file])

    issue = next(issue for issue in issues if issue.code == "missing_unit_reference")
    assert issue.severity == "error"
    assert issue.line == 1
    assert "mst30_count_value" in issue.message
    assert "unknown" in issue.message


def test_linter_rejects_numeric_descriptor_with_implicit_unknown_unit(
    tmp_path: Path,
) -> None:
    data_file = tmp_path / "implicit_unknown_unit.yaml"
    data_file.write_text(
        (
            "- model: classification_choice_descriptor\n"
            "  name: mst30_count_value\n"
            "  classification_choice_descriptor_type: numeric\n"
        ),
        encoding="utf-8",
    )

    issues = lint_kb_yaml_files([data_file])

    issue = next(
        issue for issue in issues if issue.code == "numeric_descriptor_missing_unit"
    )
    assert issue.severity == "error"
    assert "mst30_count_value" in issue.message
    assert "unknown" in issue.message


def test_linter_accepts_descriptor_with_resolved_unit(tmp_path: Path) -> None:
    data_file = tmp_path / "resolved_unit.yaml"
    data_file.write_text(
        (
            "- model: unit\n"
            "  name: count\n"
            "- model: classification_choice_descriptor\n"
            "  name: mst30_count_value\n"
            "  classification_choice_descriptor_type: numeric\n"
            "  unit: count\n"
        ),
        encoding="utf-8",
    )

    issues = lint_kb_yaml_files([data_file])

    assert not any(issue.code == "missing_unit_reference" for issue in issues)


def test_linter_flags_template_finding_without_description(tmp_path: Path) -> None:
    data_file = tmp_path / "missing_finding_description.yaml"
    data_file.write_text(
        (
            "- model: finding\n"
            "  name: withdrawal_time\n"
            "- model: report_finding\n"
            "  name: report_withdrawal_time\n"
            "  finding: withdrawal_time\n"
            "- model: report_template_section\n"
            "  name: quality\n"
            "  findings:\n"
            "    - report_withdrawal_time\n"
            "- model: report_template\n"
            "  name: colonoscopy_report\n"
            "  examination: colonoscopy\n"
            "  report_sections:\n"
            "    - quality\n"
        ),
        encoding="utf-8",
    )

    issues = lint_kb_yaml_files([data_file])
    issue = next(
        issue
        for issue in issues
        if issue.code == "template_finding_missing_description"
    )
    assert issue.severity == "warning"
    assert "withdrawal_time" in issue.message


def test_linter_accepts_described_template_finding(tmp_path: Path) -> None:
    data_file = tmp_path / "described_finding.yaml"
    data_file.write_text(
        (
            "- model: finding\n"
            "  name: withdrawal_time\n"
            "  description: Inspection withdrawal time in minutes.\n"
            "- model: report_template_section\n"
            "  name: quality\n"
            "  findings:\n"
            "    - finding: withdrawal_time\n"
            "      required: true\n"
            "- model: report_template\n"
            "  name: colonoscopy_report\n"
            "  examination: colonoscopy\n"
            "  report_sections:\n"
            "    - quality\n"
        ),
        encoding="utf-8",
    )

    issues = lint_kb_yaml_files([data_file])
    assert not any(
        issue.code == "template_finding_missing_description" for issue in issues
    )


def test_discover_yaml_files_expands_module_config(tmp_path: Path) -> None:
    module_dir = tmp_path / "module"
    data_dir = module_dir / "data"
    module_dir.mkdir()
    data_dir.mkdir()

    config_file = module_dir / "config.yaml"
    config_file.write_text(
        (
            "name: demo_module\n"
            'version: "1.0.0"\n'
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


def test_discovery_warns_when_aggregator_name_differs_from_directory(
    tmp_path: Path,
) -> None:
    child_dir = tmp_path / "child"
    child_dir.mkdir()
    (child_dir / "config.yaml").write_text(
        'name: child\nversion: "1.0.0"\ndata: {files: [], dirs: []}\n',
        encoding="utf-8",
    )
    umbrella_dir = tmp_path / "terminology"
    umbrella_dir.mkdir()
    config_file = umbrella_dir / "config.yaml"
    config_file.write_text(
        ('name: example_terminology\nversion: "1.0.0"\nmodules:\n  - child\n'),
        encoding="utf-8",
    )
    consumer_dir = tmp_path / "consumer"
    consumer_dir.mkdir()
    consumer_config = consumer_dir / "config.yaml"
    consumer_config.write_text(
        'name: consumer\nversion: "1.0.0"\nmodules:\n  - terminology\n',
        encoding="utf-8",
    )

    _, issues = discover_yaml_files(paths=[], config_paths=[consumer_config])

    issue = next(
        issue for issue in issues if issue.code == "aggregator_name_directory_mismatch"
    )
    assert issue.severity == "warning"
    assert "terminology" in issue.message
    assert "example_terminology" in issue.message


def test_lx_kb_lint_shim_imports_runtime_module(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    shim_path = repo_root / "lx_kb_lint.py"
    spec = importlib.util.spec_from_file_location("test_lx_kb_lint_shim", shim_path)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    issues = module.lint_kb_yaml_files([tmp_path / "missing.yaml"])
    assert len(issues) == 1
    assert issues[0].code == "missing_file"


def test_cli_explicit_config_does_not_include_default_modules(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_file = tmp_path / "config.yaml"
    monkeypatch.setattr(
        "sys.argv",
        ["ok", "--config", str(config_file)],
    )

    args = parse_args()

    assert args.paths == []
    assert args.config_paths == [config_file]
