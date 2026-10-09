from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from lx_dtypes.django.api.report_template_builder import (
    DEFAULT_PATIENT_INFO_FIELDS,
    GENERATED_DIR_NAME,
    BuildReportTemplatePackageRequest,
    ReportTemplateBuilderFinding,
    ReportTemplateBuilderFindingValidator,
    ReportTemplateBuilderSection,
    ReportTemplateBuilderValidatorCondition,
    SaveReportTemplateRequest,
    build_report_template_package,
    build_yaml_records,
    ensure_module_config_supports_generated_templates,
    module_dir,
    save_report_template_definition,
    slugify_name,
)


def test_slugify_name_normalizes_and_falls_back() -> None:
    assert slugify_name("  Colon Report  ") == "colon_report"
    assert slugify_name("***") == "report_template"


def study_package_payload() -> BuildReportTemplatePackageRequest:
    return BuildReportTemplatePackageRequest.model_validate(
        {
            "module_name": "coloreg",
            "module_version": "0.3.0",
            "package_name": "my_study",
            "package_version": "0.1.0",
            "depends_on": ["coloreg"],
            "file_name": "report_templates",
            "template_name": "my_study_report",
            "examination": "colonoscopy",
            "sections": [
                {
                    "section_type": "findings",
                    "name": "my_study_resection_section",
                    "findings": [
                        {
                            "finding": "coloreg_polyp_resection",
                            "multiple_allowed": True,
                            "classifications": [
                                {
                                    "classification": "coloreg_electrosurgery_settings",
                                    "required": False,
                                }
                            ],
                            "validator": {
                                "enabled": True,
                                "name": "my_study_hot_snare_requires_settings",
                                "operator": "condition",
                                "condition": {
                                    "classification": "coloreg_snare_type",
                                    "comparator": "in",
                                    "values": [
                                        "coloreg_snare_diathermic",
                                        "coloreg_snare_both",
                                    ],
                                    "then_requires": [
                                        "coloreg_electrosurgery_settings"
                                    ],
                                },
                            },
                        }
                    ],
                }
            ],
        }
    )


def test_portable_package_matches_authoring_guide_and_selects_its_rules() -> None:
    from lx_dtypes.models.interface.KnowledgeBaseConfig import KnowledgeBaseConfig
    from lx_dtypes.models.knowledge_base.validators.FindingsValidator import (
        FindingsValidator,
    )

    payload = study_package_payload()
    package = build_report_template_package(payload)
    config = yaml.safe_load(package.config_yaml)
    KnowledgeBaseConfig.model_validate(config)
    assert config == {
        "name": "my_study",
        "version": "0.1.0",
        "modules": [],
        "depends_on": ["coloreg"],
        "data": {"files": ["./report_templates.yml", "./validators.yml"]},
    }
    rules = yaml.safe_load(package.validators_yaml)
    rule = FindingsValidator.model_validate(
        {key: value for key, value in rules[0].items() if key != "model"}
    )
    assert rule.query.condition is not None
    assert rule.query.condition.any[0].values == [
        "coloreg_snare_diathermic",
        "coloreg_snare_both",
    ]
    assert rules[0]["query"]["condition"]["then_requires"] == [
        {"kind": "classification", "name": "coloreg_electrosurgery_settings"}
    ]
    templates = yaml.safe_load(package.report_templates_yaml)
    assert templates[-1]["validators"]["findings_validators"] == [rule.name]
    assert not any(record["model"] == "findings_validator" for record in templates)
    assert len(rules + templates) == len(build_yaml_records(payload))


@pytest.mark.parametrize(
    "patch",
    [
        {"package_name": "../escape"},
        {"package_name": "coloreg"},
        {"depends_on": []},
        {"depends_on": ["coloreg", "my_study"]},
        {"depends_on": ["coloreg", "coloreg"]},
        {"sections": []},
    ],
)
def test_invalid_package_configuration_is_rejected(patch: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        build_report_template_package(
            BuildReportTemplatePackageRequest.model_validate(
                {**study_package_payload().model_dump(), **patch}
            )
        )


def test_membership_rule_requires_values_and_cannot_silently_drop_requirements() -> (
    None
):
    payload = study_package_payload()
    condition = payload.sections[0].findings[0].validator.condition
    condition.values = []
    with pytest.raises(ValueError, match="require"):
        build_report_template_package(payload)
    condition.values = ["coloreg_snare_diathermic"]
    condition.then_requires = []
    with pytest.raises(ValueError, match="required classification"):
        build_report_template_package(payload)


def test_exported_package_loads_with_real_dependencies_and_executes_rules(
    tmp_path: Path,
) -> None:
    from lx_dtypes.knowledge_bases import get_packaged_knowledge_base
    from lx_dtypes.models.interface.DataLoader import DataLoader
    from lx_dtypes.models.knowledge_base.validators.ValidatorRuntime import (
        evaluate_findings_validator_runtime,
    )

    package = build_report_template_package(study_package_payload())
    target = tmp_path / package.package_name
    target.mkdir()
    for name, content in [
        ("config.yaml", package.config_yaml),
        ("report_templates.yml", package.report_templates_yaml),
        ("validators.yml", package.validators_yaml),
    ]:
        (target / name).write_text(content)
    source = get_packaged_knowledge_base("coloreg", "0.3.0").installed_data_root()
    kb = DataLoader(input_dirs=[tmp_path, source]).load_knowledge_base("my_study")
    assert kb.config is not None and kb.config.version == "0.1.0"
    rule = kb.findings_validator["my_study_hot_snare_requires_settings"]
    for choice, expected in [
        ("coloreg_snare_cold", True),
        ("coloreg_snare_diathermic", False),
        ("coloreg_snare_both", False),
    ]:
        classifications = {"coloreg_snare_type": choice}
        finding = {
            "finding": "coloreg_polyp_resection",
            "classifications": classifications,
        }
        assert (
            evaluate_findings_validator_runtime(rule, reported_findings=[finding])["ok"]
            is expected
        )
        classifications["coloreg_electrosurgery_settings"] = (
            "coloreg_electrosurgery_documented"
        )
        assert evaluate_findings_validator_runtime(rule, reported_findings=[finding])[
            "ok"
        ]


def test_duplicate_generated_rule_names_are_rejected() -> None:
    payload = study_package_payload()
    payload.sections.append(payload.sections[0].model_copy(deep=True))
    with pytest.raises(ValueError, match="record names must be unique"):
        build_report_template_package(payload)


def test_empty_membership_editor_value_is_rejected() -> None:
    payload = study_package_payload()
    condition = payload.sections[0].findings[0].validator.condition
    condition.values = []
    condition.value = ""
    with pytest.raises(ValueError, match="non-empty comparison value"):
        build_report_template_package(payload)


def test_module_dir_validates_unknown_module_and_resolves_existing(
    tmp_path: Path,
) -> None:
    module_path = tmp_path / "demo_module"
    module_path.mkdir()

    assert module_dir("demo_module", modules_root=tmp_path) == module_path.resolve()

    with pytest.raises(ValueError, match="Unknown or unsafe report-template module"):
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
        {"kind": "classification", "name": "paris_classification"}
    ]


def test_save_report_template_definition_rejects_duplicate_output_file(
    tmp_path: Path,
    terminology_root: Path,
) -> None:
    module_path = tmp_path / "demo_module"
    module_path.mkdir()
    (module_path / "config.yaml").write_text(
        yaml.safe_dump(
            {
                "name": "demo_module",
                "version": "1.0.0",
                "modules": [],
                "depends_on": [],
                "data": {"dirs": []},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    (terminology_root / "registry.json").write_text(
        json.dumps(
            {
                "modules": {
                    "demo_module": {
                        "1.0.0": {"input_dirs": [str(tmp_path)]},
                    }
                }
            }
        ),
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


def test_module_dir_does_not_alias_names_by_slugifying(tmp_path: Path) -> None:
    (tmp_path / "demo_module").mkdir()
    with pytest.raises(ValueError, match="Unknown or unsafe report-template module"):
        module_dir("demo module", modules_root=tmp_path)
