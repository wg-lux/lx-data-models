from __future__ import annotations

from lx_dtypes.models.knowledge_base.report_template.ExaminationValidator import (
    ExaminationValidator,
)
from lx_dtypes.models.knowledge_base.report_template.ReportFinding import ReportFinding
from lx_dtypes.models.knowledge_base.report_template.ReportTemplate import ReportTemplate
from lx_dtypes.models.knowledge_base.report_template.ReportTemplateSection import (
    ReportTemplateSection,
)
from lx_dtypes.models.knowledge_base.report_template.common import (
    ReportTemplateClassificationRequirement,
    ReportTemplateFindingRequirement,
    ReportTemplateSectionField,
    ReportTemplateValidators,
)


def test_report_finding_as_requirement_preserves_fields() -> None:
    report_finding = ReportFinding.model_validate(
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

    req = report_finding.as_requirement()
    assert req.finding == "esophagus_polyp"
    assert req.required is True
    assert req.multiple_allowed is False
    assert [c.classification for c in req.classifications] == ["size_mm", "shape"]
    assert [c.required for c in req.classifications] == [True, False]


def test_report_template_accepts_string_report_sections_via_list_coercion() -> None:
    template = ReportTemplate.model_validate(
        {
            "name": "t",
            "examination": "e",
            "report_sections": "baseline",
            "validators": {"examination_validators": [], "findings_validators": []},
        }
    )
    assert template.report_sections == ["baseline"]
    assert "report_sections" in ReportTemplate.list_type_fields()


def test_examination_validator_accepts_string_fields_via_list_coercion() -> None:
    ev = ExaminationValidator.model_validate(
        {
            "name": "ev",
            "finding_validators": "fv_1",
            "examination_validators": "ev_0",
        }
    )
    assert ev.finding_validators == ["fv_1"]
    assert ev.examination_validators == ["ev_0"]


def test_report_template_section_supports_mixed_finding_inputs() -> None:
    section = ReportTemplateSection.model_validate(
        {
            "name": "baseline",
            "position": 0,
            "types": ["baseline"],
            "findings": [
                "rf_polyp",
                {
                    "finding": "bleeding_site",
                    "required": False,
                    "multiple_allowed": False,
                    "classifications": [{"classification": "severity", "required": True}],
                },
            ],
        }
    )
    assert section.findings[0] == "rf_polyp"
    inline = section.findings[1]
    assert isinstance(inline, ReportTemplateFindingRequirement)
    assert inline.finding == "bleeding_site"


def test_report_template_section_defaults_preserve_existing_templates() -> None:
    section = ReportTemplateSection.model_validate(
        {
            "name": "baseline",
            "position": 0,
            "types": ["baseline"],
            "findings": ["rf_polyp"],
        }
    )

    assert section.section_kind == "findings"
    assert section.fields == []
    assert section.findings == ["rf_polyp"]


def test_report_template_section_supports_patient_history_fields() -> None:
    section = ReportTemplateSection.model_validate(
        {
            "name": "patient_context",
            "position": 0,
            "types": ["patient_data"],
            "section_kind": "patient_data",
            "fields": [
                {"key": "patient_birth_date", "required": True, "source": "patient"},
                {"key": "indication", "required": False, "source": "patient_examination"},
            ],
            "findings": [],
        }
    )

    assert section.section_kind == "patient_data"
    assert len(section.fields) == 2
    assert isinstance(section.fields[0], ReportTemplateSectionField)
    assert section.fields[0].key == "patient_birth_date"
    assert section.fields[0].required is True
    assert section.fields[1].source == "patient_examination"


def test_common_models_have_expected_defaults() -> None:
    cls_req = ReportTemplateClassificationRequirement(classification="size_mm")
    finding_req = ReportTemplateFindingRequirement(finding="esophagus_polyp")
    validators = ReportTemplateValidators()

    assert cls_req.required is False
    assert finding_req.required is False
    assert finding_req.multiple_allowed is False
    assert finding_req.classifications == []
    assert validators.examination_validators == []
    assert validators.findings_validators == []

    section_field = ReportTemplateSectionField(key="patient_gender")
    assert section_field.required is False
    assert section_field.label is None
    assert section_field.source is None
