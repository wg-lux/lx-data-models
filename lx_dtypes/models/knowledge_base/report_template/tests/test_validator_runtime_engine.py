from __future__ import annotations

from lx_dtypes.models.knowledge_base.classification.Classification import (
    Classification,
)
from lx_dtypes.models.knowledge_base.classification_choice.ClassificationChoice import (
    ClassificationChoice,
)
from lx_dtypes.models.knowledge_base.classification_choice_descriptor.ClassificationChoiceDescriptor import (
    ClassificationChoiceDescriptor,
)
from lx_dtypes.models.knowledge_base.report_template.ClassificationValidator import (
    ClassificationValidator,
)
from lx_dtypes.models.knowledge_base.report_template.ExaminationValidator import (
    ExaminationValidator,
)
from lx_dtypes.models.knowledge_base.report_template.FindingsValidator import (
    FindingsValidator,
)
from lx_dtypes.models.knowledge_base.report_template.ReportTemplate import (
    ReportTemplate,
)
from lx_dtypes.models.knowledge_base.report_template.ValidatorRuntime import (
    evaluate_classification_validator_runtime,
    evaluate_findings_validator_runtime,
    evaluate_report_template_validators_runtime,
)


def test_evaluate_findings_validator_exists_and_missing() -> None:
    exists_validator = FindingsValidator.model_validate(
        {
            "name": "finding_exists",
            "finding": "esophagus_polyp",
            "operator": "exists",
            "query": {"finding": "esophagus_polyp", "operator": "exists"},
        }
    )
    missing_validator = FindingsValidator.model_validate(
        {
            "name": "finding_missing",
            "finding": "ulcer",
            "operator": "missing",
            "query": {"finding": "ulcer", "operator": "missing"},
        }
    )

    payload = [{"finding": "esophagus_polyp", "classifications": []}]

    exists_result = evaluate_findings_validator_runtime(
        exists_validator, reported_findings=payload
    )
    missing_result = evaluate_findings_validator_runtime(
        missing_validator, reported_findings=payload
    )

    assert exists_result["ok"] is True
    assert exists_result["matched_occurrences"] == 1
    assert missing_result["ok"] is True
    assert missing_result["matched_occurrences"] == 0


def test_evaluate_findings_validator_conditional_requires_then_classifications() -> (
    None
):
    conditional_validator = FindingsValidator.model_validate(
        {
            "name": "polyp_has_lst_if_large",
            "finding": "esophagus_polyp",
            "operator": "condition",
            "query": {
                "finding": "esophagus_polyp",
                "operator": "condition",
                "condition": {
                    "all": [
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

    failing_payload = [
        {
            "finding": "esophagus_polyp",
            "classifications": [
                {"classification": "size_mm", "value": 12},
            ],
        }
    ]
    passing_payload = [
        {
            "finding": "esophagus_polyp",
            "classifications": [
                {"classification": "size_mm", "value": 12},
                {"classification": "lst", "value": "present"},
            ],
        }
    ]

    failing_result = evaluate_findings_validator_runtime(
        conditional_validator, reported_findings=failing_payload
    )
    passing_result = evaluate_findings_validator_runtime(
        conditional_validator, reported_findings=passing_payload
    )

    assert failing_result["ok"] is False
    assert failing_result["triggered_occurrences"] == 1
    assert "lst" in failing_result["missing_required_classifications"]
    assert any(
        issue["code"] == "missing_required_classification"
        for issue in failing_result["issues"]
    )

    assert passing_result["ok"] is True
    assert passing_result["triggered_occurrences"] == 1


def test_evaluate_classification_validator_exists_and_condition() -> None:
    descriptor = ClassificationChoiceDescriptor.model_validate(
        {
            "name": "size_mm_descriptor",
            "classification_choice_descriptor_type": "numeric",
        }
    )
    choice = ClassificationChoice.model_validate(
        {
            "name": "size_mm_choice",
            "classification_choice_descriptors": ["size_mm_descriptor"],
        }
    )
    classification = Classification.model_validate(
        {
            "name": "size_mm",
            "classification_choices": ["size_mm_choice"],
        }
    )
    exists_validator = ClassificationValidator.model_validate(
        {
            "name": "size_mm_required",
            "finding": "esophagus_polyp",
            "classification": "size_mm",
            "operator": "exists",
        }
    )
    condition_validator = ClassificationValidator.model_validate(
        {
            "name": "lst_required_when_large",
            "finding": "esophagus_polyp",
            "classification": "lst",
            "operator": "condition",
            "query": {
                "finding": "esophagus_polyp",
                "classification": "lst",
                "operator": "condition",
                "condition": {
                    "all": [
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

    failing_exists = evaluate_classification_validator_runtime(
        exists_validator,
        classifications={"size_mm": classification},
        classification_choices={"size_mm_choice": choice},
        classification_choice_descriptors={"size_mm_descriptor": descriptor},
        reported_findings=[{"finding": "esophagus_polyp", "classifications": []}],
    )
    failing_condition = evaluate_classification_validator_runtime(
        condition_validator,
        classifications={"size_mm": classification},
        classification_choices={"size_mm_choice": choice},
        classification_choice_descriptors={"size_mm_descriptor": descriptor},
        reported_findings=[
            {
                "finding": "esophagus_polyp",
                "classifications": [{"classification": "size_mm", "value": 12}],
            }
        ],
    )

    assert failing_exists["ok"] is False
    assert failing_exists["hint"]["data_type_hint"] == "non_categorical"
    assert failing_condition["ok"] is False
    assert failing_condition["triggered_occurrences"] == 1


def test_runtime_engine_evaluates_template_with_exam_dependencies() -> None:
    template = ReportTemplate.model_validate(
        {
            "name": "t_runtime",
            "examination": "demo_exam",
            "report_sections": [],
            "validators": {
                "classification_validators": [],
                "findings_validators": ["polyp_exists"],
                "examination_validators": ["minimum_documentation"],
            },
        }
    )

    findings_validators = {
        "polyp_exists": FindingsValidator.model_validate(
            {
                "name": "polyp_exists",
                "finding": "esophagus_polyp",
                "operator": "exists",
                "query": {"finding": "esophagus_polyp", "operator": "exists"},
            }
        )
    }
    examination_validators = {
        "minimum_documentation": ExaminationValidator.model_validate(
            {
                "name": "minimum_documentation",
                "finding_validators": ["polyp_exists"],
                "examination_validators": [],
            }
        )
    }

    failing = evaluate_report_template_validators_runtime(
        template,
        classification_validators={},
        classification_validator_names=[],
        intervention_validators={},
        unit_validators={},
        findings_validators=findings_validators,
        examination_validators=examination_validators,
        classifications={},
        classification_choices={},
        classification_choice_descriptors={},
        interventions={},
        units={},
        reported_findings=[],
    )
    passing = evaluate_report_template_validators_runtime(
        template,
        classification_validators={},
        classification_validator_names=[],
        intervention_validators={},
        unit_validators={},
        findings_validators=findings_validators,
        examination_validators=examination_validators,
        classifications={},
        classification_choices={},
        classification_choice_descriptors={},
        interventions={},
        units={},
        reported_findings=[{"finding": "esophagus_polyp", "classifications": []}],
    )

    assert failing["ok"] is False
    assert failing["findings_validators"][0]["ok"] is False
    assert failing["examination_validators"][0]["ok"] is False
    assert passing["ok"] is True
    assert passing["findings_validators"][0]["ok"] is True
    assert passing["examination_validators"][0]["ok"] is True


def test_runtime_engine_reports_unknown_and_circular_exam_validators() -> None:
    template_with_unknown = ReportTemplate.model_validate(
        {
            "name": "t_unknown",
            "examination": "demo_exam",
            "report_sections": [],
            "validators": {
                "classification_validators": [],
                "findings_validators": ["missing_validator"],
                "examination_validators": ["missing_exam_validator"],
            },
        }
    )

    unknown_result = evaluate_report_template_validators_runtime(
        template_with_unknown,
        classification_validators={},
        classification_validator_names=[],
        intervention_validators={},
        unit_validators={},
        findings_validators={},
        examination_validators={},
        classifications={},
        classification_choices={},
        classification_choice_descriptors={},
        interventions={},
        units={},
        reported_findings=[],
    )
    issue_codes = {issue["code"] for issue in unknown_result["issues"]}
    assert unknown_result["ok"] is False
    assert "unknown_findings_validator_reference" in issue_codes
    assert "unknown_examination_validator_reference" in issue_codes

    template_with_cycle = ReportTemplate.model_validate(
        {
            "name": "t_cycle",
            "examination": "demo_exam",
            "report_sections": [],
            "validators": {
                "classification_validators": [],
                "findings_validators": [],
                "examination_validators": ["exam_a"],
            },
        }
    )
    cyclic_exams = {
        "exam_a": ExaminationValidator.model_validate(
            {
                "name": "exam_a",
                "finding_validators": [],
                "examination_validators": ["exam_b"],
            }
        ),
        "exam_b": ExaminationValidator.model_validate(
            {
                "name": "exam_b",
                "finding_validators": [],
                "examination_validators": ["exam_a"],
            }
        ),
    }

    cycle_result = evaluate_report_template_validators_runtime(
        template_with_cycle,
        classification_validators={},
        classification_validator_names=[],
        intervention_validators={},
        unit_validators={},
        findings_validators={},
        examination_validators=cyclic_exams,
        classifications={},
        classification_choices={},
        classification_choice_descriptors={},
        interventions={},
        units={},
        reported_findings=[],
    )
    cycle_codes = {issue["code"] for issue in cycle_result["issues"]}
    assert cycle_result["ok"] is False
    assert "circular_examination_validator_dependency" in cycle_codes
