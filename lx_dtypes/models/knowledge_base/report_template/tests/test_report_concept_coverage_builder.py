from typing import Any

import pytest

from lx_dtypes.models.ledger.p_examination.Pydantic import PExamination
from lx_dtypes.models.knowledge_base.report_template.ReportConceptCoverageBuilder import (
    build_report_concept_coverage,
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
        {"patient": "p", "examination": "exam", "patient_findings": []}
    )


def _template() -> dict[str, Any]:
    return {
        "name": "template",
        "version": "2.0.0",
        "coverage_version": "report_concept_coverage_v1",
        "coverage_concepts": [
            {"concept_id": "present.concept", "label": "Present", "applicability_status": "required", "validator_names": ["present_validator"], "evidence_path": ["patient_findings"]},
            {"concept_id": "missing.concept", "label": "Missing", "applicability_status": "required", "validator_names": ["missing_validator"], "evidence_path": ["patient_findings", "0"]},
            {"concept_id": "conditional.concept", "label": "Conditional", "applicability_status": "conditional", "applicability_rule": "context.requires_conditional", "validator_names": ["conditional_validator"], "evidence_path": ["patient_findings"]},
            {"concept_id": "not_applicable.concept", "label": "Not applicable", "applicability_status": "not_applicable", "applicability_reason": "Not in this examination", "validator_names": ["not_applicable_validator"], "evidence_path": ["patient_findings"]},
            {"concept_id": "invalid.concept", "label": "Invalid", "applicability_status": "required", "validator_names": ["invalid_validator"], "evidence_path": ["patient_findings"]},
            {"concept_id": "unknown.concept", "label": "Unknown", "applicability_status": "required", "validator_names": ["unknown_validator"], "evidence_path": ["patient_findings"]},
        ],
    }


def test_builder_emits_runtime_statuses_and_identity() -> None:
    validation = {
        "findings_validators": [
            {"name": "present_validator", "ok": True, "issues": []},
            {"name": "missing_validator", "ok": False, "issues": [{"code": "finding_not_present"}]},
            {"name": "conditional_validator", "ok": True, "issues": []},
            {"name": "not_applicable_validator", "ok": True, "issues": []},
            {"name": "invalid_validator", "ok": False, "issues": [{"code": "bad_value"}]},
        ],
        "classification_validators": [], "intervention_validators": [],
        "examination_validators": [], "unit_validators": [],
    }
    coverage = build_report_concept_coverage(kb=_KnowledgeBase(), requested_template_name="template", template_export=_template(), p_examination=_payload(), validation=validation)
    assert [item.validation_status for item in coverage.concepts] == ["present", "missing", "present", "undetermined", "invalid", "unknown"]
    assert coverage.identity.template_version == "2.0.0"


def test_builder_rejects_template_identity_mismatch() -> None:
    with pytest.raises(ValueError, match="identity"):
        build_report_concept_coverage(kb=_KnowledgeBase(), requested_template_name="other-template", template_export=_template(), p_examination=_payload(), validation={"findings_validators": [], "classification_validators": [], "intervention_validators": [], "examination_validators": [], "unit_validators": []})


def test_builder_rejects_lexical_template_without_coverage_metadata() -> None:
    template = _template()
    template.pop("coverage_concepts")
    with pytest.raises(ValueError, match="stable concept IDs"):
        build_report_concept_coverage(kb=_KnowledgeBase(), requested_template_name="template", template_export=template, p_examination=_payload(), validation={"findings_validators": [], "classification_validators": [], "intervention_validators": [], "examination_validators": [], "unit_validators": []})
