from typing import Any

import pytest

from lx_dtypes.models.ledger.p_examination.Pydantic import PExamination
from lx_dtypes.models.knowledge_base.report_template.ReportConceptCoverageBuilder import (
    build_report_concept_coverage,
)
from lx_dtypes.models.knowledge_base.report_template.ReportTemplateCoverage import (
    ReportTemplateCoverageConcept,
)


class _Config:
    def model_dump(self, *, mode: str) -> dict[str, str]:
        assert mode == "json"
        return {"name": "module", "version": "1.0.0"}


class _KnowledgeBase:
    config = _Config()

    def model_dump(self, *, mode: str) -> dict[str, Any]:
        assert mode == "json"
        return {"config": {"name": "module", "version": "1.0.0"}}


def _payload() -> PExamination:
    return PExamination.model_validate(
        {
            "patient": "p",
            "examination": "exam",
            "patient_findings": [{"finding": "polyp", "patient_examination": "p-exam"}],
        }
    )


def _template() -> dict[str, Any]:
    return {
        "name": "template",
        "version": "2.0.0",
        "coverage_version": "report_concept_coverage_v1",
        "coverage_concepts": [
            {
                "concept_id": "present.concept",
                "label": "Present",
                "applicability_status": "required",
                "validator_names": ["present_validator"],
                "evidence_path": ["patient_findings"],
                "concept_value_path": ["patient_findings", "0", "finding"],
                "allowed_values": ["polyp"],
            },
            {
                "concept_id": "missing.concept",
                "label": "Missing",
                "applicability_status": "required",
                "validator_names": ["missing_validator"],
                "evidence_path": ["patient_findings", "1"],
                "concept_value_path": ["patient_findings", "1", "finding"],
                "allowed_values": ["mass"],
            },
            {
                "concept_id": "conditional.concept",
                "label": "Conditional",
                "applicability_status": "conditional",
                "applicability_rule": "context.requires_conditional",
                "validator_names": ["conditional_validator"],
                "evidence_path": ["patient_findings"],
                "concept_value_path": ["patient_findings", "0", "finding"],
                "allowed_values": ["polyp"],
            },
            {
                "concept_id": "not_applicable.concept",
                "label": "Not applicable",
                "applicability_status": "not_applicable",
                "applicability_reason": "Not in this examination",
                "validator_names": ["not_applicable_validator"],
                "evidence_path": ["patient_findings"],
            },
            {
                "concept_id": "invalid.concept",
                "label": "Invalid",
                "applicability_status": "required",
                "validator_names": ["invalid_validator"],
                "evidence_path": ["patient_findings"],
                "concept_value_path": ["patient_findings", "0", "finding"],
                "allowed_values": ["mass"],
            },
            {
                "concept_id": "unknown.concept",
                "label": "Unknown",
                "applicability_status": "required",
                "validator_names": ["unknown_validator"],
                "evidence_path": ["patient_findings"],
                "concept_value_path": ["patient_findings", "0", "missing_field"],
                "allowed_values": ["polyp"],
            },
        ],
    }


def test_builder_emits_runtime_statuses_and_identity() -> None:
    validation = {
        "findings_validators": [
            {"name": "present_validator", "ok": True, "issues": []},
            {
                "name": "missing_validator",
                "ok": False,
                "issues": [{"code": "finding_not_present"}],
            },
            {"name": "conditional_validator", "ok": True, "issues": []},
            {"name": "not_applicable_validator", "ok": True, "issues": []},
            {
                "name": "invalid_validator",
                "ok": False,
                "issues": [{"code": "bad_value"}],
            },
        ],
        "classification_validators": [],
        "intervention_validators": [],
        "examination_validators": [],
        "unit_validators": [],
    }
    coverage = build_report_concept_coverage(
        kb=_KnowledgeBase(),
        requested_template_name="template",
        template_export=_template(),
        p_examination=_payload(),
        validation=validation,
    )
    assert [item.validation_status for item in coverage.concepts] == [
        "present",
        "missing",
        "present",
        "undetermined",
        "invalid",
        "unknown",
    ]
    assert coverage.identity.template_version == "2.0.0"


def test_builder_rejects_template_identity_mismatch() -> None:
    with pytest.raises(ValueError, match="identity"):
        build_report_concept_coverage(
            kb=_KnowledgeBase(),
            requested_template_name="other-template",
            template_export=_template(),
            p_examination=_payload(),
            validation={
                "findings_validators": [],
                "classification_validators": [],
                "intervention_validators": [],
                "examination_validators": [],
                "unit_validators": [],
            },
        )


def test_builder_rejects_lexical_template_without_coverage_metadata() -> None:
    template = _template()
    template.pop("coverage_concepts")
    with pytest.raises(ValueError, match="stable concept IDs"):
        build_report_concept_coverage(
            kb=_KnowledgeBase(),
            requested_template_name="template",
            template_export=template,
            p_examination=_payload(),
            validation={
                "findings_validators": [],
                "classification_validators": [],
                "intervention_validators": [],
                "examination_validators": [],
                "unit_validators": [],
            },
        )


@pytest.mark.parametrize(
    ("value", "value_path", "expected"),
    [
        ("polyp", ["patient_findings", "0", "finding"], "present"),
        ("mass", ["patient_findings", "0", "finding"], "invalid"),
        ("polyp", ["patient_findings", "0", "missing_field"], "unknown"),
    ],
)
def test_builder_semantically_checks_value(
    value: str, value_path: list[str], expected: str
) -> None:
    payload = _payload().model_dump(mode="json")
    payload["patient_findings"][0]["finding"] = value
    template = {
        "name": "template",
        "version": "2.0.0",
        "coverage_version": "report_concept_coverage_v1",
        "coverage_concepts": [
            {
                "concept_id": "finding.value",
                "label": "Finding value",
                "applicability_status": "required",
                "validator_names": ["finding_validator"],
                "evidence_path": ["patient_findings", "0"],
                "concept_value_path": value_path,
                "allowed_values": ["polyp"],
            }
        ],
    }
    coverage = build_report_concept_coverage(
        kb=_KnowledgeBase(),
        requested_template_name="template",
        template_export=template,
        p_examination=PExamination.model_validate(payload),
        validation={
            "findings_validators": [{"name": "finding_validator", "ok": True}],
            "classification_validators": [],
            "intervention_validators": [],
            "examination_validators": [],
            "unit_validators": [],
        },
    )
    assert coverage.concepts[0].validation_status == expected


def test_not_applicable_does_not_require_value_rule() -> None:
    concept = ReportTemplateCoverageConcept.model_validate(
        {
            "concept_id": "not.applicable",
            "label": "Not applicable",
            "applicability_status": "not_applicable",
            "applicability_reason": "Not present in this examination",
            "validator_names": ["validator"],
            "evidence_path": ["patient_findings"],
        }
    )
    assert concept.concept_value_path is None


def _selector_template() -> dict[str, Any]:
    return {
        "name": "template",
        "version": "2.0.0",
        "coverage_version": "report_concept_coverage_v1",
        "coverage_concepts": [
            {
                "concept_id": "lesion.value",
                "label": "Lesion value",
                "applicability_status": "required",
                "validator_names": ["finding_validator"],
                "evidence_path": ["patient_findings"],
                "finding_selector": {
                    "finding_name": "lesion",
                    "classification_name": "severity",
                },
                "allowed_values": ["confirmed"],
            }
        ],
    }


def _selector_coverage(findings: list[dict[str, Any]]) -> Any:
    payload = {
        "patient": "p",
        "examination": "exam",
        "patient_findings": findings,
    }
    return build_report_concept_coverage(
        kb=_KnowledgeBase(),
        requested_template_name="template",
        template_export=_selector_template(),
        p_examination=PExamination.model_validate(payload),
        validation={
            "findings_validators": [{"name": "finding_validator", "ok": True}],
            "classification_validators": [],
            "intervention_validators": [],
            "examination_validators": [],
            "unit_validators": [],
        },
    )


def _finding_with_choice(choice: str) -> dict[str, Any]:
    return {
        "finding": "lesion",
        "patient_examination": "p-exam",
        "patient_finding_classifications": [
            {
                "patient_finding": "finding-id",
                "patient_finding_classification_choices": [
                    {
                        "classification": "severity",
                        "classification_choice": choice,
                        "patient_finding_classifications": "classification-id",
                    }
                ],
            }
        ],
    }


@pytest.mark.parametrize(
    ("findings", "expected_status", "expected_paths"),
    [
        ([], "missing", ()),
        (
            [_finding_with_choice("confirmed")],
            "present",
            (
                (
                    "patient_findings",
                    "0",
                    "patient_finding_classifications",
                    "0",
                    "patient_finding_classification_choices",
                    "0",
                ),
            ),
        ),
        (
            [
                {"finding": "other", "patient_examination": "p-exam"},
                _finding_with_choice("confirmed"),
                _finding_with_choice("confirmed"),
            ],
            "present",
            (
                (
                    "patient_findings",
                    "1",
                    "patient_finding_classifications",
                    "0",
                    "patient_finding_classification_choices",
                    "0",
                ),
                (
                    "patient_findings",
                    "2",
                    "patient_finding_classifications",
                    "0",
                    "patient_finding_classification_choices",
                    "0",
                ),
            ),
        ),
        (
            [{"finding": "lesion", "patient_examination": "p-exam"}],
            "unknown",
            (("patient_findings", "0", "patient_finding_classifications"),),
        ),
        (
            [_finding_with_choice("uncertain")],
            "invalid",
            (
                (
                    "patient_findings",
                    "0",
                    "patient_finding_classifications",
                    "0",
                    "patient_finding_classification_choices",
                    "0",
                ),
            ),
        ),
    ],
)
def test_finding_selector_resolves_all_instances(
    findings: list[dict[str, Any]],
    expected_status: str,
    expected_paths: tuple[tuple[str, ...], ...],
) -> None:
    coverage = _selector_coverage(findings)
    item = coverage.concepts[0]
    assert item.validation_status == expected_status
    assert item.evidence_paths == expected_paths


def test_finding_selector_does_not_hide_invalid_later_instance() -> None:
    findings = [
        _finding_with_choice("confirmed"),
        _finding_with_choice("uncertain"),
    ]
    coverage = _selector_coverage(findings)
    assert coverage.concepts[0].validation_status == "invalid"
    assert coverage.concepts[0].evidence_paths == (
        (
            "patient_findings",
            "0",
            "patient_finding_classifications",
            "0",
            "patient_finding_classification_choices",
            "0",
        ),
        (
            "patient_findings",
            "1",
            "patient_finding_classifications",
            "0",
            "patient_finding_classification_choices",
            "0",
        ),
    )


def test_finding_selector_rejects_choice_without_classification_name() -> None:
    with pytest.raises(ValueError, match="classification_name"):
        ReportTemplateCoverageConcept.model_validate(
            {
                "concept_id": "invalid.selector",
                "label": "Invalid selector",
                "applicability_status": "required",
                "validator_names": ["validator"],
                "evidence_path": ["patient_findings"],
                "finding_selector": {
                    "finding_name": "lesion",
                    "classification_choice": "confirmed",
                },
                "allowed_values": ["confirmed"],
            }
        )
