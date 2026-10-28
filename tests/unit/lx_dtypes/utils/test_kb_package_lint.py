from pathlib import Path

import pytest

from lx_dtypes.models.interface.DataLoader import DataLoader
from lx_dtypes.scripts import lint_kb_yaml as cli
from lx_dtypes.utils.kb_package_lint import check_kb_package


def module(root: Path, name: str, records: str, dependencies: str = "") -> Path:
    directory = root / name
    directory.mkdir(parents=True)
    config = directory / "config.yaml"
    config.write_text(
        f'name: {name}\nversion: "1.0.0"\n{dependencies}'
        "data:\n  files: [records.yml]\n",
        encoding="utf-8",
    )
    # CLI scenarios use complete display labels unless testing coverage itself.
    import yaml

    payload = yaml.safe_load(records)
    for record in payload:
        record.setdefault("name_de", "Bezeichnung")
        record.setdefault("name_en", "Display name")
    (directory / "records.yml").write_text(
        yaml.safe_dump(payload, sort_keys=False), encoding="utf-8"
    )
    return config


def run(monkeypatch: pytest.MonkeyPatch, *args: str) -> int:
    monkeypatch.setattr("sys.argv", ["ok", *args])
    return cli.main()


@pytest.mark.parametrize("selector", ["file", "dir"])
def test_lint_uses_runtime_data_selectors(tmp_path: Path, selector: str) -> None:
    config = module(tmp_path, "terms", "- model: finding\n  name: selected\n")
    records = config.parent / "records.yml"
    value = "records.yml"
    if selector == "dir":
        (config.parent / "data").mkdir()
        records = records.rename(config.parent / "data/records.yml")
        value = "data"
    config.write_text(f'name: terms\nversion: "1.0.0"\ndata:\n  {selector}: {value}\n')
    result = check_kb_package(config)
    assert not result.issues
    assert result.knowledge_base is not None
    assert "selected" in result.knowledge_base.finding
    assert result.files == (records,)


def test_semantic_module_names_resolve_in_current_release_scope(tmp_path: Path) -> None:
    root = tmp_path / "data"
    current = module(root / "terminology", "renamed_folder", "[]")
    current.write_text(
        current.read_text().replace("name: renamed_folder", "name: terms")
    )
    retained = module(root / "terminology/versions/release/1.0.0", "terms", "[]")
    config = module(root / "report_templates", "report", "[]", "depends_on: [terms]\n")
    runtime = DataLoader(input_dirs=[root]).resolved_module_configs("report")
    assert {item.source_file for item in runtime} == {config, current}
    assert retained not in {item.source_file for item in runtime}
    result = check_kb_package(config)
    assert not result.issues
    assert set(result.files) == {
        config.parent / "records.yml",
        current.parent / "records.yml",
    }


def test_equally_scoped_candidates_are_rejected(tmp_path: Path) -> None:
    for folder in ("first", "second"):
        config = module(tmp_path, folder, "[]")
        config.write_text(config.read_text().replace(f"name: {folder}", "name: terms"))
    config = module(tmp_path, "report", "[]", "depends_on: [terms]\n")
    result = check_kb_package(config)
    assert result.knowledge_base is None
    assert any(
        issue.code == "module_resolution_error" and "ambiguous" in issue.message
        for issue in result.issues
    )


def test_default_scope_is_all_current_packages_and_strict(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    current = module(tmp_path / "terminology", "terms", "[]")
    reporting = module(tmp_path / "report_templates", "reporting", "[]")
    module(tmp_path / "terminology" / "versions", "old", "[]")
    monkeypatch.setattr(cli, "package_data_root", lambda: tmp_path)
    monkeypatch.setattr("sys.argv", ["ok"])
    args = cli.parse_args()
    assert set(args.config_paths) == {current, reporting}
    assert args.strict_aliases and args.strict_mixed_styles and args.fail_on_warnings


def test_independent_packages_do_not_conflict(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    first = module(
        tmp_path,
        "first",
        "- model: finding\n  name: shared\n  description: First meaning\n",
    )
    second = module(
        tmp_path,
        "second",
        "- model: finding\n  name: shared\n  description: Different meaning\n",
    )
    assert run(monkeypatch, "--config", str(first), "--config", str(second)) == 0
    assert "0 error(s), 0 warning(s)" in capsys.readouterr().out


def test_inherited_reporting_warnings_fail_by_default(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module(tmp_path, "terms", "- model: finding\n  name: canonical\n")
    module(
        tmp_path,
        "report",
        "- model: report_finding\n  name: reference\n  finding: canonical\n",
        "depends_on: [terms]\n",
    )
    study = module(
        tmp_path,
        "study",
        "- model: finding\n  name: custom\n",
        "depends_on: [report]\n",
    )
    assert run(monkeypatch, "--config", str(study)) == 1
    output = capsys.readouterr().out
    assert "report_template_concept_definition" in output
    assert "study/records.yml:1:3" in output
    assert "0 error(s), 1 warning(s)" in output
    assert run(monkeypatch, "--config", str(study), "--no-fail-on-warnings") == 0
    assert "1 warning(s)" in capsys.readouterr().out


def test_grouped_runtime_warning_preserves_all_lint_locations(tmp_path: Path) -> None:
    module(tmp_path, "terms", "- model: finding\n  name: canonical\n")
    module(
        tmp_path,
        "report",
        "- model: report_finding\n  name: reference\n  finding: canonical\n",
        "depends_on: [terms]\n",
    )
    config = module(
        tmp_path,
        "study",
        "- model: finding\n  name: first\n- model: finding\n  name: second\n",
        "depends_on: [report]\n",
    )
    result = check_kb_package(config)
    issues = [
        issue
        for issue in result.issues
        if issue.code == "report_template_concept_definition"
    ]
    assert len(issues) == 2
    assert {issue.file for issue in issues} == {config.parent / "records.yml"}
    assert len({issue.line for issue in issues}) == 2
    assert all(issue.column == 3 and issue.severity == "warning" for issue in issues)
    for issue, name in zip(issues, ("first", "second"), strict=True):
        assert f"'finding' definition '{name}'" in issue.message


@pytest.mark.parametrize(
    "records,diagnostic",
    [
        (
            "- model: finding\n  name: wrong\n  invented_field: true\n",
            "package_load_error",
        ),
        (
            "- model: report_template\n  name: broken\n  examination: missing\n  report_sections: [absent]\n",
            "unknown_template_examination",
        ),
    ],
)
def test_schema_and_template_failures_are_reported(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    records: str,
    diagnostic: str,
) -> None:
    config = module(tmp_path, "invalid", records)
    assert run(monkeypatch, "--config", str(config)) == 1
    output = capsys.readouterr().out
    assert diagnostic in output
    assert "Traceback" not in output


def test_dependency_conflict_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module(tmp_path, "terms", "- model: finding\n  name: shared\n")
    report = module(
        tmp_path,
        "report",
        "- model: finding\n  name: shared\n",
        "depends_on: [terms]\n",
    )
    assert run(monkeypatch, str(report)) == 1
    output = capsys.readouterr().out
    assert "duplicate_name" in output
    assert "terms/records.yml:1:3" in output
    assert "report/records.yml:1:3" in output


def test_raw_file_schema_checks_and_scope_are_explicit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    file = tmp_path / "records.yml"
    file.write_text("- model: report_template\n  name: missing_required_examination\n")
    assert run(monkeypatch, str(file)) == 1
    output = capsys.readouterr().out
    assert "invalid_model" in output
    assert "File-only checks" in output


def test_missing_config_does_not_prevent_other_package_checks(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    report = module(
        tmp_path,
        "report",
        "- model: finding\n  name: local\n- model: report_finding\n  name: reference\n  finding: local\n",
    )
    assert (
        run(
            monkeypatch,
            "--config",
            str(tmp_path / "missing" / "config.yaml"),
            "--config",
            str(report),
        )
        == 1
    )
    output = capsys.readouterr().out
    assert "missing_config" in output
    assert "report_template_concept_definition" in output


def test_duplicate_manifest_keys_are_errors(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    config = module(tmp_path, "duplicate", "[]")
    config.write_text(config.read_text() + "name: shadowed\n")
    assert run(monkeypatch, "--config", str(config)) == 1
    output = capsys.readouterr().out
    assert "Duplicate YAML mapping key 'name'" in output


def test_unrelated_invalid_manifest_does_not_break_selected_package(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config = module(tmp_path, "valid", "- model: finding\n  name: local\n")
    invalid = module(tmp_path, "unrelated", "[]")
    invalid.write_text("name: unrelated\nversion: []\n")
    assert run(monkeypatch, "--config", str(config)) == 0


@pytest.mark.parametrize("missing_validator", [False, True])
def test_template_readiness_and_source_locations(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    missing_validator: bool,
) -> None:
    module(
        tmp_path,
        "terms",
        "- model: examination\n  name: exam\n- model: finding\n  name: canonical\n  description: A recorded observation\n",
    )
    config = module(
        tmp_path,
        "report",
        "- model: report_template_section\n  name: section\n  findings: [canonical]\n- model: report_template\n  name: template\n  examination: exam\n  report_sections: [section]\n"
        + (
            "  validators:\n    findings_validators: [missing]\n"
            if missing_validator
            else ""
        ),
        "depends_on: [terms]\n",
    )
    assert run(monkeypatch, "--config", str(config), "--no-fail-on-warnings") == int(
        missing_validator
    )
    output = capsys.readouterr().out
    if missing_validator:
        assert "unknown_findings_validator_reference" in output
        assert "report/records.yml:7:3" in output
        assert "1 error(s)" in output
    else:
        assert "0 error(s), 0 warning(s)" in output


def test_explicit_releases_with_same_name_are_independent(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    first = module(tmp_path, "first", "- model: finding\n  name: shared\n")
    second = module(tmp_path, "second", "- model: finding\n  name: shared\n")
    second.write_text(
        second.read_text()
        .replace("name: second", "name: first")
        .replace('"1.0.0"', '"2.0.0"')
    )
    assert run(monkeypatch, "--config", str(first), "--config", str(second)) == 0
    assert "0 error(s), 0 warning(s)" in capsys.readouterr().out


def test_empty_file_selection_is_not_success(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run(monkeypatch, str(tmp_path)) == 1
    assert "no_yaml_files" in capsys.readouterr().out


@pytest.mark.parametrize(
    "name",
    [
        "finding_v2",
        "finding_v2_legacy",
        "finding_version_3",
        "finding@1.0.0",
        "finding_1_0_0",
        "finding_1.2.3",
    ],
)
def test_versions_belong_in_version_fields(tmp_path: Path, name: str) -> None:
    from lx_dtypes.utils.kb_yaml_lint import lint_kb_yaml_files

    file = tmp_path / "records.yml"
    file.write_text(
        f"- model: finding\n  name: {name}\n  name_de: Befund\n  name_en: Finding\n"
    )
    issues = lint_kb_yaml_files([file], check_authoring=True)
    assert [issue.code for issue in issues] == ["version_in_name"]
    assert issues[0].severity == "error"
    assert issues[0].line == 1


@pytest.mark.parametrize(
    "name",
    [
        "size_6_9",
        "size_10_19",
        "paris_0_ii_a",
        "upper_gi_quality_2025",
        "star_upper_gi_cleanliness_total_0_9",
    ],
)
def test_clinical_numbers_are_not_versions(tmp_path: Path, name: str) -> None:
    from lx_dtypes.utils.kb_yaml_lint import lint_kb_yaml_files

    file = tmp_path / "records.yml"
    file.write_text(
        f"- model: finding\n  name: {name}\n  name_de: Befund\n  name_en: Finding\n"
    )
    assert not lint_kb_yaml_files([file], check_authoring=True)


@pytest.mark.parametrize("english", [None, "", "  ", "unknown", 123])
def test_authored_language_coverage_cannot_be_filled_by_model_defaults(
    tmp_path: Path, english: object
) -> None:
    import yaml

    from lx_dtypes.utils.kb_yaml_lint import lint_kb_yaml_files

    file = tmp_path / "records.yml"
    file.write_text(
        yaml.safe_dump(
            [
                {
                    "model": "finding",
                    "name": "finding",
                    "name_de": "Befund",
                    "name_en": english,
                }
            ]
        )
    )
    issues = lint_kb_yaml_files([file], check_authoring=True)
    assert [issue.code for issue in issues] == ["missing_language_coverage"]
    assert "name_en" in issues[0].message
    assert "name_de" not in issues[0].message


def test_section_titles_supply_language_coverage(tmp_path: Path) -> None:
    from lx_dtypes.utils.kb_yaml_lint import lint_kb_yaml_files

    file = tmp_path / "records.yml"
    file.write_text(
        "- model: report_template_section\n  name: section\n  title_de: Abschnitt\n  title_en: Section\n"
    )
    assert not lint_kb_yaml_files([file], check_authoring=True)


def test_cli_enforces_language_and_package_name_guards(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    config = module(tmp_path, "study_v2", "- model: finding\n  name: finding\n")
    (config.parent / "records.yml").write_text(
        "- model: finding\n  name: finding\n  name_de: Befund\n"
    )
    assert run(monkeypatch, "--config", str(config)) == 1
    output = capsys.readouterr().out
    assert "version_in_name" in output
    assert "missing_language_coverage" in output
    assert "name_en" in output
