from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from lx_dtypes.models.knowledge_base.report_template.TemplateReadiness import (
    ReportTemplateLifecycleStatusLiteral,
    ReportTemplateReadinessSummaryDataDict,
)
from lx_dtypes.utils.report_template_registry import (
    set_report_template_lifecycle_status,
)

MODULES_ROOT = Path(__file__).resolve().parents[2] / "data"
GENERATED_DIR_NAME = "generated_templates"

DEFAULT_PATIENT_INFO_FIELDS = [
    {"key": "first_name", "label": "Vorname", "source": "patient", "required": False},
    {"key": "last_name", "label": "Nachname", "source": "patient", "required": False},
    {
        "key": "patient_birth_date",
        "label": "Geburtsdatum",
        "source": "patient",
        "required": False,
    },
    {
        "key": "patient_gender",
        "label": "Geschlecht",
        "source": "patient",
        "required": False,
    },
    {
        "key": "indication",
        "label": "Indikation",
        "source": "patient_examination",
        "required": False,
    },
]


def slugify_name(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", str(value or "").strip().lower())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized or "report_template"


class ReportTemplateBuilderField(BaseModel):
    key: str = Field(min_length=1)
    label: str = ""
    source: Literal["patient", "patient_examination", "history"] = "patient"
    required: bool = False


class ReportTemplateBuilderClassification(BaseModel):
    classification: str = Field(min_length=1)
    required: bool = False


class ReportTemplateBuilderValidatorCondition(BaseModel):
    classification: str = ""
    comparator: Literal["eq", "ne", "gt", "gte", "lt", "lte", "in", "not_in"] = "eq"
    value: Any = None
    then_requires: list[str] = Field(default_factory=list)


class ReportTemplateBuilderFindingValidator(BaseModel):
    enabled: bool = False
    name: str = ""
    operator: Literal["exists", "missing", "condition"] = "exists"
    condition: ReportTemplateBuilderValidatorCondition = Field(
        default_factory=ReportTemplateBuilderValidatorCondition
    )

    @model_validator(mode="after")
    def validate_condition_payload(self) -> "ReportTemplateBuilderFindingValidator":
        if not self.enabled or self.operator != "condition":
            return self
        if not self.condition.classification.strip():
            raise ValueError(
                "Condition validators require a classification to compare against."
            )
        return self


class ReportTemplateBuilderFinding(BaseModel):
    finding: str = Field(min_length=1)
    required: bool = False
    multiple_allowed: bool = False
    classifications: list[ReportTemplateBuilderClassification] = Field(
        default_factory=list
    )
    validator: ReportTemplateBuilderFindingValidator = Field(
        default_factory=ReportTemplateBuilderFindingValidator
    )


class ReportTemplateBuilderSection(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str | None = None
    section_type: Literal["logo", "patient_info", "clinic_address", "findings"]
    name: str = Field(min_length=1)
    description: str = ""
    fields: list[ReportTemplateBuilderField] = Field(default_factory=list)
    findings: list[ReportTemplateBuilderFinding] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_section_shape(self) -> "ReportTemplateBuilderSection":
        if self.section_type == "findings" and not self.findings:
            raise ValueError("Findings sections must contain at least one finding.")
        if self.section_type != "findings" and self.findings:
            raise ValueError("Only findings sections may define findings.")
        return self


class SaveReportTemplateRequest(BaseModel):
    module_name: str = "report_template_examples"
    file_name: str = Field(min_length=1)
    template_name: str = Field(min_length=1)
    examination: str = Field(min_length=1)
    description: str = ""
    sections: list[ReportTemplateBuilderSection] = Field(default_factory=list)


class SaveReportTemplateResponse(BaseModel):
    module_name: str
    file_name: str
    path: str
    template_name: str
    records_written: int
    lifecycle_status: ReportTemplateLifecycleStatusLiteral = "draft"
    readiness: ReportTemplateReadinessSummaryDataDict | None = None


class PublishReportTemplateResponse(BaseModel):
    module_name: str
    template_name: str
    lifecycle_status: ReportTemplateLifecycleStatusLiteral
    readiness: ReportTemplateReadinessSummaryDataDict | None = None


class ReportTemplateModuleLocation(BaseModel):
    module_name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    modules_root: Path


def module_dir(module_name: str, *, modules_root: Path | None = None) -> Path:
    modules_root = modules_root or MODULES_ROOT
    safe_name = slugify_name(module_name)
    resolved = (modules_root / safe_name).resolve()
    root_resolved = modules_root.resolve()
    if root_resolved not in resolved.parents and resolved != root_resolved:
        raise ValueError("Invalid report-template module path.")
    if not resolved.exists():
        raise ValueError(f"Unknown report-template module '{module_name}'.")
    return resolved


def ensure_module_config_supports_generated_templates(module_path: Path) -> None:
    config_path = module_path / "config.yaml"
    if not config_path.exists():
        raise ValueError(f"Module config is missing: {config_path}")

    loaded = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"Module config has invalid shape: {config_path}")

    data = loaded.setdefault("data", {})
    if not isinstance(data, dict):
        raise ValueError(f"Module config data section must be a mapping: {config_path}")

    dirs = data.setdefault("dirs", [])
    if not isinstance(dirs, list):
        raise ValueError(f"Module config data.dirs must be a list: {config_path}")

    generated_entry = f"./{GENERATED_DIR_NAME}"
    if generated_entry not in dirs:
        dirs.append(generated_entry)
        config_path.write_text(
            yaml.safe_dump(loaded, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )

    (module_path / GENERATED_DIR_NAME).mkdir(parents=True, exist_ok=True)


def _build_section_fields(
    section: ReportTemplateBuilderSection,
) -> list[dict[str, Any]]:
    if section.section_type != "patient_info":
        return []

    if not section.fields:
        return [dict(item) for item in DEFAULT_PATIENT_INFO_FIELDS]

    return [
        {
            "key": field.key.strip(),
            "label": field.label.strip() or field.key.strip(),
            "source": field.source,
            "required": field.required,
        }
        for field in section.fields
    ]


def _build_report_finding_record(
    section_slug: str,
    index: int,
    finding_row: ReportTemplateBuilderFinding,
) -> tuple[str, dict[str, Any]]:
    finding_name = finding_row.finding.strip()
    report_finding_name = (
        f"{section_slug}_finding_{index + 1}_{slugify_name(finding_name)}"
    )
    classifications = [
        {
            "classification": classification.classification.strip(),
            "required": classification.required,
        }
        for classification in finding_row.classifications
    ]

    return report_finding_name, {
        "model": "report_finding",
        "name": report_finding_name,
        "finding": finding_name,
        "required": finding_row.required,
        "multiple_allowed": finding_row.multiple_allowed,
        "classifications": classifications,
    }


def _build_findings_validator_record(
    template_slug: str,
    section_slug: str,
    index: int,
    finding_row: ReportTemplateBuilderFinding,
) -> dict[str, Any] | None:
    validator = finding_row.validator
    if not validator.enabled:
        return None

    finding_name = finding_row.finding.strip()
    validator_name = validator.name.strip() or (
        f"{template_slug}_{section_slug}_{index + 1}_{validator.operator}"
    )
    validator_name = slugify_name(validator_name)

    record: dict[str, Any] = {
        "model": "findings_validator",
        "name": validator_name,
        "finding": finding_name,
        "operator": validator.operator,
        "query": {
            "finding": finding_name,
            "operator": validator.operator,
        },
    }

    if validator.operator == "condition":
        then_requires = [
            {"classification": classification.strip()}
            for classification in validator.condition.then_requires
            if classification.strip()
        ]
        record["query"]["condition"] = {
            "any": [
                {
                    "classification": validator.condition.classification.strip(),
                    "comparator": validator.condition.comparator,
                    "value": validator.condition.value,
                }
            ],
            "then_requires": then_requires,
        }

    return record


def build_yaml_records(payload: SaveReportTemplateRequest) -> list[dict[str, Any]]:
    template_slug = slugify_name(payload.template_name)
    records: list[dict[str, Any]] = []
    report_section_names: list[str] = []
    findings_validator_names: list[str] = []

    for section_index, section in enumerate(payload.sections):
        section_slug = slugify_name(section.name)
        section_record: dict[str, Any] = {
            "model": "report_template_section",
            "name": section_slug,
            "description": section.description.strip(),
            "position": section_index,
            "types": [section.section_type],
            "findings": [],
        }

        if section.section_type == "findings":
            section_record["section_kind"] = "findings"
            for finding_index, finding_row in enumerate(section.findings):
                report_finding_name, report_finding_record = (
                    _build_report_finding_record(
                        section_slug, finding_index, finding_row
                    )
                )
                records.append(report_finding_record)
                section_record["findings"].append(report_finding_name)

                validator_record = _build_findings_validator_record(
                    template_slug, section_slug, finding_index, finding_row
                )
                if validator_record is not None:
                    findings_validator_names.append(str(validator_record["name"]))
                    records.append(validator_record)
        else:
            section_record["section_kind"] = "patient_data"
            section_record["fields"] = _build_section_fields(section)

        report_section_names.append(section_slug)
        records.append(section_record)

    records.append(
        {
            "model": "report_template",
            "name": payload.template_name.strip(),
            "description": payload.description.strip(),
            "examination": payload.examination.strip(),
            "report_sections": report_section_names,
            "validators": {
                "examination_validators": [],
                "findings_validators": findings_validator_names,
            },
        }
    )

    return records


def save_report_template_definition(
    payload: SaveReportTemplateRequest,
    *,
    modules_root: Path | None = None,
) -> SaveReportTemplateResponse:
    modules_root = modules_root or MODULES_ROOT
    module_name = payload.module_name.strip() or "report_template_examples"
    module_path = module_dir(module_name, modules_root=modules_root)
    ensure_module_config_supports_generated_templates(module_path)

    output_path = (
        module_path / GENERATED_DIR_NAME / f"{slugify_name(payload.file_name)}.yaml"
    )
    if output_path.exists():
        raise FileExistsError(f"Template file already exists: {output_path.name}")

    records = build_yaml_records(payload)
    output_path.write_text(
        yaml.safe_dump(records, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    set_report_template_lifecycle_status(
        module_path, payload.template_name.strip(), "draft"
    )

    return SaveReportTemplateResponse(
        module_name=module_name,
        file_name=output_path.name,
        path=str(output_path),
        template_name=payload.template_name.strip(),
        records_written=len(records),
        lifecycle_status="draft",
    )


def set_saved_report_template_lifecycle(
    *,
    module_name: str,
    template_name: str,
    lifecycle_status: ReportTemplateLifecycleStatusLiteral,
    modules_root: Path | None = None,
) -> PublishReportTemplateResponse:
    modules_root = modules_root or MODULES_ROOT
    module_path = module_dir(module_name, modules_root=modules_root)
    set_report_template_lifecycle_status(module_path, template_name, lifecycle_status)
    return PublishReportTemplateResponse(
        module_name=module_name,
        template_name=template_name,
        lifecycle_status=lifecycle_status,
    )
