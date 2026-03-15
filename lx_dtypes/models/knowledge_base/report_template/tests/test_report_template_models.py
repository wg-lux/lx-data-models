from __future__ import annotations

import pytest
from pydantic import ValidationError

from lx_dtypes.models.knowledge_base.report_template.FindingsValidator import (
    DeprecatedReportTemplateValueWarning,
)
from lx_dtypes.models.knowledge_base.report_template.ReportFinding import (
    ReportTemplateClassificationRequirement,
    ReportTemplateFindingRequirement,
)
from lx_dtypes.models.knowledge_base.report_template.ExaminationValidator import (
    ExaminationValidator,
)
from lx_dtypes.models.knowledge_base.report_template.FindingsValidator import (
    FindingsValidator,
)
from lx_dtypes.models.knowledge_base.report_template.ReportFinding import ReportFinding
from lx_dtypes.models.knowledge_base.report_template.ReportTemplate import (
    ReportTemplate,
    ReportTemplateValidators,
)
from lx_dtypes.models.knowledge_base.report_template.ReportTemplateSection import (
    ReportTemplateSection,
    ReportTemplateSectionField,
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


def test_findings_validator_query_supports_condition_shape() -> None:
    fv = FindingsValidator.model_validate(
        {
            "name": "polyp_has_lst_if_large",
            "finding": "esophagus_polyp",
            "operator": "condition",
            "query": {
                "finding": "esophagus_polyp",
                "operator": "condition",
                "condition": {
                    "any": [
                        {
                            "classification": "size_mm",
                            "comparator": "gt",
                            "value": 10,
                        }
                    ],
                    "then_requires": [{"classification": "lst"}],
                },
            },
        }
    )

    assert fv.query.finding == "esophagus_polyp"
    assert fv.query.operator == "condition"
    assert fv.operator == "condition"
    condition = fv.query.condition
    assert condition is not None
    assert condition.any[0].classification == "size_mm"
    assert condition.then_requires == [{"classification": "lst"}]


def test_findings_validator_operator_asd_is_rejected() -> None:
    with pytest.raises(ValidationError):
        FindingsValidator.model_validate(
            {
                "name": "legacy_asd_operator",
                "finding": "esophagus_polyp",
                "operator": "ASD",
                "query": {"finding": "esophagus_polyp", "operator": "ASD"},
            }
        )


def test_findings_validator_comparator_alias_normalizes_with_warning() -> None:
    with pytest.warns(DeprecatedReportTemplateValueWarning, match=">"):
        fv = FindingsValidator.model_validate(
            {
                "name": "legacy_comparator_alias",
                "finding": "esophagus_polyp",
                "operator": "condition",
                "query": {
                    "finding": "esophagus_polyp",
                    "operator": "condition",
                    "condition": {
                        "any": [
                            {
                                "classification": "size_mm",
                                "comparator": ">",
                                "value": 10,
                            }
                        ]
                    },
                },
            }
        )

    assert fv.query.condition is not None
    assert fv.query.operator == "condition"
    assert fv.query.condition.any[0].comparator == "gt"


def test_findings_validator_rejects_legacy_conditional_operator() -> None:
    with pytest.raises(
        ValidationError, match="Unsupported findings_validator.operator"
    ):
        FindingsValidator.model_validate(
            {
                "name": "legacy_conditional_alias",
                "finding": "esophagus_polyp",
                "operator": "conditional",
                "query": {
                    "finding": "esophagus_polyp",
                    "operator": "conditional",
                    "condition": {
                        "any": [
                            {
                                "classification": "size_mm",
                                "comparator": "gt",
                                "value": 10,
                            }
                        ]
                    },
                },
            }
        )


def test_findings_validator_query_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        FindingsValidator.model_validate(
            {
                "name": "invalid",
                "finding": "esophagus_polyp",
                "operator": "exists",
                "query": {
                    "finding": "esophagus_polyp",
                    "operator": "exists",
                    "unexpected_key": "nope",
                },
            }
        )


def test_findings_validator_query_rejects_unknown_operator() -> None:
    with pytest.raises(ValidationError):
        FindingsValidator.model_validate(
            {
                "name": "invalid_operator",
                "finding": "esophagus_polyp",
                "operator": "unsupported_op",
                "query": {
                    "finding": "esophagus_polyp",
                    "operator": "unsupported_op",
                },
            }
        )


def test_findings_validator_query_rejects_unknown_comparator() -> None:
    with pytest.raises(ValidationError):
        FindingsValidator.model_validate(
            {
                "name": "invalid_comparator",
                "finding": "esophagus_polyp",
                "operator": "condition",
                "query": {
                    "finding": "esophagus_polyp",
                    "operator": "condition",
                    "condition": {
                        "any": [
                            {
                                "classification": "size_mm",
                                "comparator": "around",
                                "value": 10,
                            }
                        ]
                    },
                },
            }
        )


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
                    "classifications": [
                        {"classification": "severity", "required": True}
                    ],
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
                {
                    "key": "indication",
                    "required": False,
                    "source": "patient_examination",
                },
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
