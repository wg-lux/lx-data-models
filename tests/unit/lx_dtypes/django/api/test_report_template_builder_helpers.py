from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from lx_dtypes.django.api.report_template_builder import (
    DEFAULT_PATIENT_INFO_FIELDS,
    GENERATED_DIR_NAME,
    ReportTemplateBuilderFinding,
    ReportTemplateBuilderFindingValidator,
    ReportTemplateBuilderSection,
    ReportTemplateBuilderValidatorCondition,
    SaveReportTemplateRequest,
    build_yaml_records,
    ensure_module_config_supports_generated_templates,
    module_dir,
    save_report_template_definition,
    slugify_name,
)


def test_slugify_name_normalizes_and_falls_back() -> None:
    assert slugify_name("  Colon Report  ") == "colon_report"
    assert slugify_name("***") == "report_template"


def test_module_dir_validates_unknown_module_and_resolves_existing(
    tmp_path: Path,
) -> None:
    module_path = tmp_path / "demo_module"
    module_path.mkdir()

    assert module_dir("demo module", modules_root=tmp_path) == module_path.resolve()

    with pytest.raises(ValueError, match="Unknown report-template module"):
        module_dir("missing", modules_root=tmp_path)


def test_ensure_module_config_supports_generated_templates_normalizes_null_config(
    tmp_path: Path,
) -> None:
    module_path = tmp_path / "demo"
    module_path.mkdir()
    config_path = module_path / "config.yaml"
    config_path.write_text("null\n", encoding="utf-8")

    ensure_module_config_supports_generated_templates(module_path)

    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert payload["data"]["dirs"] == [f"./{GENERATED_DIR_NAME}"]
    assert (module_path / GENERATED_DIR_NAME).is_dir()


@pytest.mark.parametrize(
    ("config_payload", "expected_message"),
    [
        ({"data": []}, "Module config data section must be a mapping"),
        ({"data": {"dirs": {}}}, "Module config data.dirs must be a list"),
    ],
)
def test_ensure_module_config_supports_generated_templates_rejects_invalid_shapes(
    tmp_path: Path, config_payload: object, expected_message: str
) -> None:
    module_path = tmp_path / "demo"
    module_path.mkdir()
    (module_path / "config.yaml").write_text(
        yaml.safe_dump(config_payload, sort_keys=False),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=expected_message):
        ensure_module_config_supports_generated_templates(module_path)


def test_ensure_module_config_supports_generated_templates_adds_generated_dir(
    tmp_path: Path,
) -> None:
    module_path = tmp_path / "demo"
    module_path.mkdir()
    config_path = module_path / "config.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {"name": "demo", "data": {"dirs": ["./existing"]}}, sort_keys=False
        ),
        encoding="utf-8",
    )

    ensure_module_config_supports_generated_templates(module_path)
    ensure_module_config_supports_generated_templates(module_path)

    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert payload["data"]["dirs"].count(f"./{GENERATED_DIR_NAME}") == 1
    assert (module_path / GENERATED_DIR_NAME).is_dir()


def test_build_yaml_records_adds_default_patient_fields_and_condition_validator() -> (
    None
):
    payload = SaveReportTemplateRequest(
        module_name="demo_module",
        module_version="1.0.0",
        file_name="custom_report",
        template_name="Custom Report",
        examination="colonoscopy",
        sections=[
            ReportTemplateBuilderSection(
                section_type="patient_info",
                name="Patient Info",
            ),
            ReportTemplateBuilderSection(
                section_type="findings",
                name="Main Findings",
                findings=[
                    ReportTemplateBuilderFinding(
                        finding="colon_polyp",
                        validator=ReportTemplateBuilderFindingValidator(
                            enabled=True,
                            operator="condition",
                            condition=ReportTemplateBuilderValidatorCondition(
                                classification="size_mm",
                                comparator="gte",
                                value=10,
                                then_requires=["paris_classification", ""],
                            ),
                        ),
                    )
                ],
            ),
        ],
    )

    records = build_yaml_records(payload)
    patient_section = next(
        r
        for r in records
        if r["model"] == "report_template_section" and r["name"] == "patient_info"
    )
    assert patient_section["fields"] == DEFAULT_PATIENT_INFO_FIELDS

    findings_validator = next(r for r in records if r["model"] == "findings_validator")
    assert findings_validator["query"]["condition"]["any"][0] == {
        "classification": "size_mm",
        "comparator": "gte",
        "value": 10,
    }
    assert findings_validator["query"]["condition"]["then_requires"] == [
        {"classification": "paris_classification"}
    ]


def test_save_report_template_definition_rejects_duplicate_output_file(
    tmp_path: Path,
) -> None:
    module_path = tmp_path / "demo_module"
    module_path.mkdir()
    (module_path / "config.yaml").write_text(
        yaml.safe_dump({"name": "demo_module", "data": {"dirs": []}}, sort_keys=False),
        encoding="utf-8",
    )
    generated_dir = module_path / GENERATED_DIR_NAME
    generated_dir.mkdir()
    (generated_dir / "custom_report.yaml").write_text("[]", encoding="utf-8")

    payload = SaveReportTemplateRequest(
        module_name="demo_module",
        module_version="1.0.0",
        file_name="custom_report",
        template_name="Custom Report",
        examination="colonoscopy",
        sections=[
            ReportTemplateBuilderSection(
                section_type="patient_info",
                name="Patient",
            )
        ],
    )

    with pytest.raises(FileExistsError, match="Template file already exists"):
        save_report_template_definition(
            payload, resolved_version="1.0.0", modules_root=tmp_path
        )
