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
from lx_dtypes.models.knowledge_base.intervention.Intervention import Intervention
from lx_dtypes.models.knowledge_base.report_template.ClassificationValidator import (
    ClassificationValidator,
)
from lx_dtypes.models.knowledge_base.report_template.ExaminationValidator import (
    ExaminationValidator,
)
from lx_dtypes.models.knowledge_base.report_template.FindingsValidator import (
    FindingsValidator,
)
from lx_dtypes.models.knowledge_base.report_template.InterventionValidator import (
    InterventionValidator,
)
from lx_dtypes.models.knowledge_base.report_template.ReportTemplate import (
    ReportTemplate,
)
from lx_dtypes.models.knowledge_base.report_template.UnitValidator import (
    UnitValidator,
)
from lx_dtypes.models.knowledge_base.report_template.ValidatorRuntime import (
    evaluate_classification_validator_runtime,
    evaluate_findings_validator_runtime,
    evaluate_report_template_validators_runtime,
)
from lx_dtypes.models.knowledge_base.unit.Unit import Unit


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


def test_evaluate_findings_validator_reports_missing_condition_data() -> None:
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

    result = evaluate_findings_validator_runtime(
        conditional_validator,
        reported_findings=[{"finding": "esophagus_polyp", "classifications": []}],
    )

    assert result["ok"] is False
    assert result["triggered_occurrences"] == 0
    assert result["missing_required_classifications"] == []
    assert result["issues"][0]["code"] == "missing_data_requirement"
    assert result["issues"][0]["level"] == "warning"
    assert result["issues"][0]["details"] == {
        "occurrence_index": 0,
        "missing_condition_classifications": ["size_mm"],
    }


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
    optional_exists_validator = ClassificationValidator.model_validate(
        {
            "name": "optional_size_if_polyp_present",
            "finding": "esophagus_polyp",
            "classification": "size_mm",
            "operator": "exists",
            "precedence": "optional",
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
    absent_optional_exists = evaluate_classification_validator_runtime(
        optional_exists_validator,
        classifications={"size_mm": classification},
        classification_choices={"size_mm_choice": choice},
        classification_choice_descriptors={"size_mm_descriptor": descriptor},
        reported_findings=[],
    )
    choice_only_exists = evaluate_classification_validator_runtime(
        exists_validator,
        classifications={"size_mm": classification},
        classification_choices={"size_mm_choice": choice},
        classification_choice_descriptors={"size_mm_descriptor": descriptor},
        reported_findings=[
            {
                "finding": "esophagus_polyp",
                "classifications": [
                    {"classification": "size_mm", "value": "size_mm_choice"}
                ],
            }
        ],
    )
    valued_exists = evaluate_classification_validator_runtime(
        exists_validator,
        classifications={"size_mm": classification},
        classification_choices={"size_mm_choice": choice},
        classification_choice_descriptors={"size_mm_descriptor": descriptor},
        reported_findings=[
            {
                "finding": "esophagus_polyp",
                "classifications": [
                    {"classification": "size_mm", "value": "size_mm_choice"},
                    {"classification": "size_mm", "value": 12},
                ],
            }
        ],
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
    assert absent_optional_exists["ok"] is True
    assert failing_exists["hint"]["data_type_hint"] == "non_categorical"
    assert choice_only_exists["ok"] is False
    assert choice_only_exists["issues"][0]["code"] == (
        "classification_value_not_present"
    )
    assert valued_exists["ok"] is True
    assert failing_condition["ok"] is False
    assert failing_condition["triggered_occurrences"] == 1


def test_evaluate_classification_validator_reports_missing_condition_data() -> None:
    validator = ClassificationValidator.model_validate(
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

    result = evaluate_classification_validator_runtime(
        validator,
        classifications={},
        classification_choices={},
        classification_choice_descriptors={},
        reported_findings=[{"finding": "esophagus_polyp", "classifications": []}],
    )

    assert result["ok"] is False
    assert result["triggered_occurrences"] == 0
    assert result["issues"][0]["code"] == "missing_data_requirement"
    assert result["issues"][0]["details"] == {
        "occurrence_index": 0,
        "missing_condition_classifications": ["size_mm"],
    }


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


def test_runtime_engine_simulates_medical_template_execution() -> None:
    template = ReportTemplate.model_validate(
        {
            "name": "upper_gi_polyp_template",
            "examination": "gastroscopy",
            "report_sections": [],
            "validators": {
                "classification_validators": ["lst_required_when_large"],
                "intervention_validators": ["biopsy_required_when_large"],
                "findings_validators": ["polyp_has_lst_if_large"],
                "examination_validators": ["minimum_polyp_documentation"],
                "unit_validators": ["size_mm_unit_when_large"],
            },
        }
    )
    size_condition = {
        "all": [
            {
                "classification": "size_mm",
                "comparator": "gt",
                "value": 10,
            }
        ]
    }
    findings_validators = {
        "polyp_has_lst_if_large": FindingsValidator.model_validate(
            {
                "name": "polyp_has_lst_if_large",
                "finding": "esophagus_polyp",
                "operator": "condition",
                "query": {
                    "finding": "esophagus_polyp",
                    "operator": "condition",
                    "condition": {
                        **size_condition,
                        "then_requires": [{"classification": "lst"}],
                    },
                },
            }
        )
    }
    classification_validators = {
        "lst_required_when_large": ClassificationValidator.model_validate(
            {
                "name": "lst_required_when_large",
                "finding": "esophagus_polyp",
                "classification": "lst",
                "operator": "condition",
                "query": {
                    "finding": "esophagus_polyp",
                    "classification": "lst",
                    "operator": "condition",
                    "condition": size_condition,
                },
            }
        )
    }
    intervention_validators = {
        "biopsy_required_when_large": InterventionValidator.model_validate(
            {
                "name": "biopsy_required_when_large",
                "finding": "esophagus_polyp",
                "intervention": "biopsy",
                "operator": "condition",
                "query": {
                    "finding": "esophagus_polyp",
                    "intervention": "biopsy",
                    "operator": "condition",
                    "condition": size_condition,
                },
            }
        )
    }
    unit_validators = {
        "size_mm_unit_when_large": UnitValidator.model_validate(
            {
                "name": "size_mm_unit_when_large",
                "finding": "esophagus_polyp",
                "classification": "size_mm",
                "unit": "mm",
                "operator": "condition",
                "query": {
                    "finding": "esophagus_polyp",
                    "classification": "size_mm",
                    "unit": "mm",
                    "operator": "condition",
                    "condition": size_condition,
                },
            }
        )
    }
    examination_validators = {
        "minimum_polyp_documentation": ExaminationValidator.model_validate(
            {
                "name": "minimum_polyp_documentation",
                "finding_validators": ["polyp_has_lst_if_large"],
                "examination_validators": [],
            }
        )
    }

    common_kwargs = {
        "template": template,
        "classification_validators": classification_validators,
        "intervention_validators": intervention_validators,
        "unit_validators": unit_validators,
        "findings_validators": findings_validators,
        "examination_validators": examination_validators,
        "classifications": {
            "lst": Classification.model_validate({"name": "lst"}),
            "size_mm": Classification.model_validate({"name": "size_mm"}),
        },
        "classification_choices": {},
        "classification_choice_descriptors": {},
        "interventions": {
            "biopsy": Intervention.model_validate(
                {"name": "biopsy", "intervention_types": ["sampling"]}
            )
        },
        "units": {
            "mm": Unit.model_validate(
                {"name": "mm", "abbreviation": "mm", "unit_types": ["length"]}
            )
        },
    }

    missing_source_data = evaluate_report_template_validators_runtime(
        **common_kwargs,
        reported_findings=[{"finding": "esophagus_polyp", "classifications": []}],
    )
    incomplete_large_polyp = evaluate_report_template_validators_runtime(
        **common_kwargs,
        reported_findings=[
            {
                "finding": "esophagus_polyp",
                "classifications": [{"classification": "size_mm", "value": 12}],
                "interventions": [],
            }
        ],
    )
    complete_large_polyp = evaluate_report_template_validators_runtime(
        **common_kwargs,
        reported_findings=[
            {
                "finding": "esophagus_polyp",
                "classifications": [
                    {"classification": "size_mm", "value": 12, "unit": "mm"},
                    {"classification": "lst", "value": "present"},
                ],
                "interventions": ["biopsy"],
            }
        ],
    )

    assert missing_source_data["ok"] is False
    assert {
        issue["validator_kind"]
        for issue in missing_source_data["issues"]
        if issue["code"] == "missing_data_requirement"
    } == {
        "classification_validator",
        "intervention_validator",
        "findings_validator",
        "unit_validator",
    }
    assert "failed_finding_validator_dependency" in {
        issue["code"] for issue in missing_source_data["issues"]
    }
    assert all(
        issue["level"] == "warning"
        for issue in missing_source_data["issues"]
        if issue["code"] == "missing_data_requirement"
    )

    incomplete_issue_codes = {
        issue["code"] for issue in incomplete_large_polyp["issues"]
    }
    assert incomplete_large_polyp["ok"] is False
    assert "missing_required_classification" in incomplete_issue_codes
    assert "missing_required_intervention" in incomplete_issue_codes
    assert "missing_required_unit" in incomplete_issue_codes
    assert incomplete_large_polyp["classification_validators"][0]["ok"] is False
    assert incomplete_large_polyp["intervention_validators"][0]["ok"] is False
    assert incomplete_large_polyp["unit_validators"][0]["ok"] is False

    assert complete_large_polyp["ok"] is True
    assert complete_large_polyp["issues"] == []
    assert complete_large_polyp["evaluated_findings_count"] == 1
    assert complete_large_polyp["findings_validators"][0]["triggered_occurrences"] == 1
    assert complete_large_polyp["classification_validators"][0]["ok"] is True
    assert complete_large_polyp["intervention_validators"][0]["ok"] is True
    assert complete_large_polyp["unit_validators"][0]["ok"] is True
