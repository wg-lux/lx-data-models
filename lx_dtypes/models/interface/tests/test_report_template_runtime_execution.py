from pathlib import Path

import pytest

from lx_dtypes.models.interface.DataLoader import DataLoader
from lx_dtypes.models.interface.KnowledgeBase import SemanticAdmissibilityError
from lx_dtypes.models.knowledge_base.report_template import (
    build_report_concept_coverage,
)
from lx_dtypes.models.knowledge_base.report_template.ValidatorRuntime import (
    evaluate_classification_validator_runtime,
    evaluate_findings_validator_runtime,
)
from lx_dtypes.models.ledger.p_examination.Pydantic import PExamination
from lx_dtypes.models.ledger.p_finding.Pydantic import PFinding
from lx_dtypes.models.ledger.p_finding_classification_choice.Pydantic import (
    PFindingClassificationChoice,
)
from lx_dtypes.models.ledger.p_finding_classification_choice_descriptor.Pydantic import (
    PFindingClassificationChoiceDescriptor,
)
from lx_dtypes.models.ledger.p_finding_classifications.Pydantic import (
    PFindingClassifications,
)
from lx_dtypes.models.ledger.p_indication.Pydantic import PIndication
from lx_dtypes.models.ledger.p_indication_classification.Pydantic import (
    PIndicationClassification,
)
from lx_dtypes.models.ledger.p_indication_classification_descriptor.Pydantic import (
    PIndicationClassificationDescriptor,
)
from lx_dtypes.models.ledger.p_intervention.Pydantic import PFindingIntervention
from lx_dtypes.models.ledger.p_interventions.Pydantic import PFindingInterventions


DATA_ROOT = Path(__file__).resolve().parents[3] / "data"


def _build_p_examination(
    findings_payload: list[dict[str, object]],
    *,
    examination: str = "star_upper_gi_endoscopy",
    indications_payload: list[dict[str, object]] | None = None,
    examiners: list[str] | None = None,
) -> PExamination:
    p_examination = PExamination.model_validate(
        {
            "patient": "test_patient",
            "examiners": examiners or [],
            "examination": examination,
            "patient_findings": [],
            "patient_indications": [],
        }
    )

    for finding_payload in findings_payload:
        p_finding = PFinding.model_validate(
            {
                "finding": finding_payload["finding"],
                "patient_examination": str(p_examination.uuid),
                "patient_finding_classifications": [],
                "patient_finding_interventions": [],
            }
        )

        classification_payloads = finding_payload.get("classifications", [])
        if isinstance(classification_payloads, list) and classification_payloads:
            p_classifications = PFindingClassifications.model_validate(
                {
                    "patient_finding": str(p_finding.uuid),
                    "patient_finding_classification_choices": [],
                }
            )
            for classification_payload in classification_payloads:
                if not isinstance(classification_payload, dict):
                    continue
                raw_value = classification_payload.get("value", "present")
                classification_choice = classification_payload.get(
                    "classification_choice"
                )
                if not isinstance(classification_choice, str):
                    if isinstance(raw_value, str):
                        classification_choice = raw_value
                    else:
                        classification_choice = str(
                            classification_payload["classification"]
                        )
                p_choice = PFindingClassificationChoice.model_validate(
                    {
                        "classification": classification_payload["classification"],
                        "classification_choice": classification_choice,
                        "patient_finding_classifications": str(p_classifications.uuid),
                        "patient_finding_classification_choice_descriptors": [],
                    }
                )
                descriptor_value = classification_payload.get("descriptor_value")
                if descriptor_value is not None or not isinstance(raw_value, str):
                    p_choice.patient_finding_classification_choice_descriptors.append(
                        PFindingClassificationChoiceDescriptor.model_validate(
                            {
                                "descriptor_value": (
                                    descriptor_value
                                    if descriptor_value is not None
                                    else raw_value
                                ),
                                "classification_choice_descriptor": (
                                    classification_payload.get(
                                        "descriptor",
                                        "length_mm_descriptor",
                                    )
                                ),
                                "patient_finding_classification_choice": str(
                                    p_choice.uuid
                                ),
                            }
                        )
                    )
                p_classifications.patient_finding_classification_choices.append(
                    p_choice
                )
            p_finding.patient_finding_classifications.append(p_classifications)

        p_examination.patient_findings.append(p_finding)

    for indication_payload in indications_payload or []:
        p_indication = PIndication.model_validate(
            {
                "indication": indication_payload["indication"],
                "patient_examination": str(p_examination.uuid),
                "patient_indication_classifications": [],
            }
        )
        indication_classifications = indication_payload.get("classifications", [])
        if not isinstance(indication_classifications, list):
            indication_classifications = []
        for classification_payload in indication_classifications:
            if not isinstance(classification_payload, dict):
                continue
            raw_value = classification_payload.get("value", "present")
            classification_choice = classification_payload.get("classification_choice")
            if not isinstance(classification_choice, str):
                if isinstance(raw_value, str):
                    classification_choice = raw_value
                else:
                    classification_choice = str(
                        classification_payload["classification"]
                    )
            p_classification = PIndicationClassification.model_validate(
                {
                    "classification": classification_payload["classification"],
                    "classification_choice": classification_choice,
                    "patient_indication": str(p_indication.uuid),
                    "patient_indication_classification_descriptors": [],
                }
            )
            if not isinstance(raw_value, str):
                p_classification.patient_indication_classification_descriptors.append(
                    PIndicationClassificationDescriptor.model_validate(
                        {
                            "descriptor_value": raw_value,
                            "classification_choice_descriptor": (
                                "length_mm_descriptor"
                            ),
                            "patient_indication_classification": str(
                                p_classification.uuid
                            ),
                        }
                    )
                )
            p_indication.patient_indication_classifications.append(p_classification)
        p_examination.patient_indications.append(p_indication)

    return p_examination


def test_knowledge_base_runtime_execution_for_example_template() -> None:
    loader = DataLoader(input_dirs=[DATA_ROOT])
    loader.load_module_configs()
    kb = loader.load_knowledge_base("report_template_examples")

    failing = kb.evaluate_report_template_validators(
        "star_upper_gi_main",
        p_examination=_build_p_examination(
            [
                {
                    "finding": "star_upper_gi_mucosa_esophagus_abnormal",
                    "classifications": [],
                },
                {
                    "finding": "esophagus_polyp",
                    "classifications": [
                        {"classification": "size_mm", "value": 12},
                    ],
                },
            ]
        ),
    )
    passing = kb.evaluate_report_template_validators(
        "star_upper_gi_main",
        p_examination=_build_p_examination(
            [
                {
                    "finding": "star_upper_gi_mucosa_esophagus_abnormal",
                    "classifications": [],
                },
                {
                    "finding": "esophagus_polyp",
                    "classifications": [
                        {"classification": "size_mm", "value": 12},
                        {"classification": "lst", "value": "present"},
                    ],
                },
            ]
        ),
    )

    assert failing["ok"] is False
    assert any(
        issue["code"] == "missing_required_classification"
        for issue in failing["issues"]
    )
    assert failing["classification_validators"]
    assert failing["classification_validators"][0]["hint"]["precedence"] == "required"
    assert passing["ok"] is True


def test_colonoscopy_template_emits_authoritative_concept_coverage() -> None:
    loader = DataLoader(input_dirs=[DATA_ROOT])
    loader.load_module_configs()
    kb = loader.load_knowledge_base("report_template_examples")
    p_examination = _build_p_examination(
        [
            {
                "finding": "endoscopy_hardware_used",
                "classifications": [
                    {
                        "classification": (
                            "endoscopy_hardware_endoscope_processor_model"
                        ),
                        "value": "olympus_cv_190",
                    },
                    {
                        "classification": "endoscopy_hardware_serial_number",
                        "classification_choice": (
                            "endoscopy_hardware_serial_number_recorded"
                        ),
                        "descriptor": "endoscopy_hardware_serial_number_value",
                        "descriptor_value": "SN-TEST-190-001",
                    },
                ],
            },
            {
                "finding": "sedation_endoscopy",
                "classifications": [
                    {"classification": "sedation_performed", "value": "yes"},
                    {
                        "classification": "examination_setting_generic_sedation",
                        "value": "sedation_propofol",
                    },
                ],
            },
            {
                "finding": "endoscopy_preprocedure_risk_assessment_checklist",
                "classifications": [
                    {
                        "classification": "endoscopy_risk_assessment_time",
                        "classification_choice": "endoscopy_risk_assessment_time_recorded",
                        "descriptor": "endoscopy_risk_assessment_time_value",
                        "descriptor_value": "09:50",
                    },
                    {
                        "classification": "risk_assessment_protocol_version",
                        "classification_choice": "risk_assessment_protocol_version_recorded",
                        "descriptor": "risk_assessment_protocol_version_value",
                        "descriptor_value": "DGVS Sign-in 2025",
                    },
                    {
                        "classification": "patient_record_and_required_documents_review_status",
                        "value": "assessment_confirmed_complete",
                    },
                    {
                        "classification": "required_laboratory_and_prior_result_review_status",
                        "value": "assessment_no_items_required",
                    },
                    {
                        "classification": "procedure_preparation_review_status",
                        "value": "assessment_confirmed_complete",
                    },
                    {
                        "classification": "fasting_requirement_review_status",
                        "value": "fasting_requirement_confirmed_met",
                    },
                    {
                        "classification": "asa_review_status",
                        "value": "asa_current_class_reviewed",
                    },
                    {
                        "classification": "airway_risk_review_status",
                        "value": "assessment_reviewed_none_identified",
                    },
                    {
                        "classification": "mallampati_review_status",
                        "value": "mallampati_assessment_reviewed",
                    },
                    {
                        "classification": "cardiopulmonary_risk_review_status",
                        "value": "assessment_reviewed_none_identified",
                    },
                    {
                        "classification": "medication_review_status",
                        "value": "medication_reviewed_none_relevant",
                    },
                    {
                        "classification": "antithrombotic_management_review_status",
                        "value": "anticoagulant_management_not_applicable",
                    },
                    {
                        "classification": "antibiotic_prophylaxis_assessment_status",
                        "value": "antibiotic_prophylaxis_not_indicated",
                    },
                    {
                        "classification": "allergy_review_status",
                        "value": "assessment_reviewed_none_identified",
                    },
                    {
                        "classification": "infection_review_status",
                        "value": "assessment_reviewed_none_identified",
                    },
                    {
                        "classification": "dental_status_review_status",
                        "value": "dental_status_assessed_no_relevant_issue",
                    },
                    {
                        "classification": "glaucoma_review_status",
                        "value": "assessment_reviewed_none_identified",
                    },
                ],
            },
            {
                "finding": "endoscopy_preprocedure_asa_assessment",
                "classifications": [
                    {
                        "classification": "asa_physical_status_classification",
                        "value": "asa_class_ii",
                    }
                ],
            },
            {
                "finding": "endoscopy_preprocedure_physical_assessment",
                "classifications": [
                    {
                        "classification": "preprocedure_physical_assessment_time",
                        "classification_choice": "preprocedure_physical_assessment_time_recorded",
                        "descriptor": "preprocedure_physical_assessment_time_value",
                        "descriptor_value": "09:52",
                    },
                    {
                        "classification": "preprocedure_heart_rate",
                        "classification_choice": "preprocedure_heart_rate_recorded",
                        "descriptor": "preprocedure_heart_rate_value",
                        "value": 72,
                    },
                    {
                        "classification": "preprocedure_systolic_blood_pressure",
                        "classification_choice": "preprocedure_systolic_blood_pressure_recorded",
                        "descriptor": "preprocedure_systolic_blood_pressure_value",
                        "value": 125,
                    },
                    {
                        "classification": "preprocedure_diastolic_blood_pressure",
                        "classification_choice": "preprocedure_diastolic_blood_pressure_recorded",
                        "descriptor": "preprocedure_diastolic_blood_pressure_value",
                        "value": 78,
                    },
                    {
                        "classification": "preprocedure_oxygen_saturation",
                        "classification_choice": "preprocedure_oxygen_saturation_recorded",
                        "descriptor": "preprocedure_oxygen_saturation_value",
                        "value": 98,
                    },
                    {
                        "classification": "preprocedure_cardiac_auscultation_status",
                        "value": "auscultation_no_relevant_abnormality",
                    },
                    {
                        "classification": "preprocedure_pulmonary_auscultation_status",
                        "value": "auscultation_no_relevant_abnormality",
                    },
                ],
            },
            {
                "finding": "endoscopy_preprocedure_last_oral_intake",
                "classifications": [
                    {
                        "classification": "last_oral_intake_time",
                        "classification_choice": "last_oral_intake_time_recorded",
                        "descriptor": "last_oral_intake_time_value",
                        "descriptor_value": "06:00",
                    },
                    {
                        "classification": "last_oral_intake_type",
                        "classification_choice": "last_oral_intake_type_recorded",
                        "descriptor": "last_oral_intake_type_value",
                        "descriptor_value": "Klare Flüssigkeit",
                    },
                ],
            },
            {
                "finding": "endoscopy_medication_status",
                "classifications": [
                    {
                        "classification": ("endoscopy_medication_documentation_status"),
                        "value": "documented_none",
                    }
                ],
            },
            {
                "finding": "endoscopy_process_timestamps",
                "classifications": [
                    {
                        "classification": "endoscopy_room_entry_time",
                        "classification_choice": "endoscopy_room_entry_time_recorded",
                        "descriptor": "endoscopy_room_entry_time_value",
                        "descriptor_value": "10:00",
                    },
                    {
                        "classification": "endoscope_insertion_time",
                        "classification_choice": "endoscope_insertion_time_recorded",
                        "descriptor": "endoscope_insertion_time_value",
                        "descriptor_value": "10:10",
                    },
                    {
                        "classification": "colonoscopy_withdrawal_start_time",
                        "classification_choice": (
                            "colonoscopy_withdrawal_start_time_recorded"
                        ),
                        "descriptor": "colonoscopy_withdrawal_start_time_value",
                        "descriptor_value": "10:25",
                    },
                    {
                        "classification": "endoscope_removal_time",
                        "classification_choice": "endoscope_removal_time_recorded",
                        "descriptor": "endoscope_removal_time_value",
                        "descriptor_value": "10:35",
                    },
                    {
                        "classification": "endoscopy_room_exit_time",
                        "classification_choice": "endoscopy_room_exit_time_recorded",
                        "descriptor": "endoscopy_room_exit_time_value",
                        "descriptor_value": "10:40",
                    },
                    {
                        "classification": "endoscopy_department_exit_time",
                        "classification_choice": (
                            "endoscopy_department_exit_time_recorded"
                        ),
                        "descriptor": "endoscopy_department_exit_time_value",
                        "descriptor_value": "11:00",
                    },
                ],
            },
            {
                "finding": "endoscopy_preprocedure_team_timeout",
                "classifications": [
                    {
                        "classification": "endoscopy_team_timeout_time",
                        "classification_choice": (
                            "endoscopy_team_timeout_time_recorded"
                        ),
                        "descriptor": "endoscopy_team_timeout_time_value",
                        "descriptor_value": "10:05",
                    },
                    {
                        "classification": "team_introduction_status",
                        "value": "team_introduction_not_applicable",
                    },
                    {
                        "classification": ("patient_identity_confirmation_status"),
                        "value": "patient_identity_confirmed_against_identifiers",
                    },
                    {
                        "classification": ("patient_preparation_confirmation_status"),
                        "value": "patient_preparation_confirmed",
                    },
                    {
                        "classification": (
                            "planned_procedure_and_special_features_review_status"
                        ),
                        "value": "procedure_confirmed_no_special_features",
                    },
                    {
                        "classification": (
                            "patient_specific_risk_and_special_medication_review_status"
                        ),
                        "value": "risks_reviewed_none_identified",
                    },
                    {
                        "classification": ("required_documents_confirmation_status"),
                        "value": "required_documents_confirmed_complete",
                    },
                    {
                        "classification": "required_equipment_readiness_status",
                        "value": "required_equipment_confirmed_ready",
                    },
                    {
                        "classification": "required_personnel_readiness_status",
                        "value": "required_personnel_confirmed_ready",
                    },
                ],
            },
            {
                "finding": "endoscopy_postprocedure_sign_out",
                "classifications": [
                    {
                        "classification": "endoscopy_sign_out_time",
                        "classification_choice": "endoscopy_sign_out_time_recorded",
                        "descriptor": "endoscopy_sign_out_time_value",
                        "descriptor_value": "10:38",
                    },
                    {
                        "classification": (
                            "postprocedure_patient_condition_documentation_status"
                        ),
                        "value": "postprocedure_patient_condition_documented",
                    },
                    {
                        "classification": "follow_up_measures_confirmation_status",
                        "value": "follow_up_confirmed_no_special_measures",
                    },
                    {
                        "classification": ("specimen_handling_reconciliation_status"),
                        "value": "specimen_handling_not_applicable",
                    },
                    {
                        "classification": "procedure_problem_review_status",
                        "value": "procedure_problems_reviewed_none",
                    },
                    {
                        "classification": "report_documentation_completeness_status",
                        "value": "report_documentation_confirmed_complete",
                    },
                ],
            },
            {
                "finding": "endoscopy_sedation_monitoring_measurement",
                "classifications": [
                    {
                        "classification": "sedation_monitoring_time",
                        "classification_choice": "sedation_monitoring_time_recorded",
                        "descriptor": "sedation_monitoring_time_value",
                        "descriptor_value": "10:30",
                    },
                    {
                        "classification": "sedation_heart_rate",
                        "classification_choice": "sedation_heart_rate_recorded",
                        "descriptor": "sedation_heart_rate_value",
                        "value": 72,
                    },
                    {
                        "classification": "sedation_systolic_blood_pressure",
                        "classification_choice": (
                            "sedation_systolic_blood_pressure_recorded"
                        ),
                        "descriptor": "sedation_systolic_blood_pressure_value",
                        "value": 125,
                    },
                    {
                        "classification": "sedation_diastolic_blood_pressure",
                        "classification_choice": (
                            "sedation_diastolic_blood_pressure_recorded"
                        ),
                        "descriptor": "sedation_diastolic_blood_pressure_value",
                        "value": 78,
                    },
                    {
                        "classification": "sedation_oxygen_saturation",
                        "classification_choice": (
                            "sedation_oxygen_saturation_recorded"
                        ),
                        "descriptor": "sedation_oxygen_saturation_value",
                        "value": 98,
                    },
                ],
            },
            {
                "finding": "endoscopy_supplemental_oxygen_administration",
                "classifications": [
                    {
                        "classification": "supplemental_oxygen_delivery_and_flow",
                        "classification_choice": "oxygen_delivery_nasal_cannula",
                        "descriptor": "supplemental_oxygen_flow_rate_value",
                        "value": 2,
                    }
                ],
            },
            {
                "finding": "endoscopy_intravenous_fluid_status",
                "classifications": [
                    {
                        "classification": "intravenous_fluid_documentation_status",
                        "value": "documented_none",
                    }
                ],
            },
            {
                "finding": "endoscopy_post_sedation_recovery_assessment",
                "classifications": [
                    {
                        "classification": "sedation_monitoring_time",
                        "classification_choice": "sedation_monitoring_time_recorded",
                        "descriptor": "sedation_monitoring_time_value",
                        "descriptor_value": "10:50",
                    },
                    {
                        "classification": "sedation_heart_rate",
                        "classification_choice": "sedation_heart_rate_recorded",
                        "descriptor": "sedation_heart_rate_value",
                        "value": 70,
                    },
                    {
                        "classification": "sedation_systolic_blood_pressure",
                        "classification_choice": (
                            "sedation_systolic_blood_pressure_recorded"
                        ),
                        "descriptor": "sedation_systolic_blood_pressure_value",
                        "value": 122,
                    },
                    {
                        "classification": "sedation_diastolic_blood_pressure",
                        "classification_choice": (
                            "sedation_diastolic_blood_pressure_recorded"
                        ),
                        "descriptor": "sedation_diastolic_blood_pressure_value",
                        "value": 76,
                    },
                    {
                        "classification": "sedation_oxygen_saturation",
                        "classification_choice": (
                            "sedation_oxygen_saturation_recorded"
                        ),
                        "descriptor": "sedation_oxygen_saturation_value",
                        "value": 99,
                    },
                    {
                        "classification": "post_sedation_orientation_status",
                        "value": "post_sedation_fully_oriented",
                    },
                ],
            },
            {
                "finding": ("endoscopy_post_sedation_discharge_or_transfer_assessment"),
                "classifications": [
                    {
                        "classification": "sedation_monitoring_time",
                        "classification_choice": "sedation_monitoring_time_recorded",
                        "descriptor": "sedation_monitoring_time_value",
                        "descriptor_value": "11:00",
                    },
                    {
                        "classification": "sedation_heart_rate",
                        "classification_choice": "sedation_heart_rate_recorded",
                        "descriptor": "sedation_heart_rate_value",
                        "value": 68,
                    },
                    {
                        "classification": "sedation_systolic_blood_pressure",
                        "classification_choice": (
                            "sedation_systolic_blood_pressure_recorded"
                        ),
                        "descriptor": "sedation_systolic_blood_pressure_value",
                        "value": 120,
                    },
                    {
                        "classification": "sedation_diastolic_blood_pressure",
                        "classification_choice": (
                            "sedation_diastolic_blood_pressure_recorded"
                        ),
                        "descriptor": "sedation_diastolic_blood_pressure_value",
                        "value": 75,
                    },
                    {
                        "classification": "sedation_oxygen_saturation",
                        "classification_choice": (
                            "sedation_oxygen_saturation_recorded"
                        ),
                        "descriptor": "sedation_oxygen_saturation_value",
                        "value": 99,
                    },
                    {
                        "classification": "post_sedation_orientation_status",
                        "value": "post_sedation_fully_oriented",
                    },
                    {
                        "classification": "post_sedation_disposition",
                        "value": "post_sedation_outpatient_discharge",
                    },
                ],
            },
            {
                "finding": "bowel_preparation_lc",
                "classifications": [
                    {
                        "classification": "bowel_prep_boston",
                        "value": "bowel_prep_boston_3",
                    }
                ],
            },
            {
                "finding": "bowel_preparation_tc",
                "classifications": [
                    {
                        "classification": "bowel_prep_boston",
                        "value": "bowel_prep_boston_3",
                    }
                ],
            },
            {
                "finding": "bowel_preparation_rc",
                "classifications": [
                    {
                        "classification": "bowel_prep_boston",
                        "value": "bowel_prep_boston_3",
                    }
                ],
            },
            {
                "finding": "bowel_preparation_bbps_total",
                "classifications": [
                    {
                        "classification": "bowel_prep_boston_total",
                        "value": "bbps_total_9",
                    }
                ],
            },
            {
                "finding": "colonoscopy_deepest_viewed_location",
                "classifications": [
                    {
                        "classification": "colonoscopy_location_default",
                        "value": "cecum",
                    }
                ],
            },
            {
                "finding": "colonoscopy_withdrawal_time_minutes",
                "classifications": [
                    {
                        "classification": "time_minutes_generic",
                        "classification_choice": "minutes_numeric_value",
                        "descriptor": "minutes_numeric_value",
                        "value": 9,
                    }
                ],
            },
            {
                "finding": "colonoscopy_cecal_landmarks_photodocumented",
                "classifications": [
                    {
                        "classification": "appendiceal_orifice_photodocumented",
                        "value": "yes",
                    },
                    {
                        "classification": "ileocecal_valve_photodocumented",
                        "value": "yes",
                    },
                    {
                        "classification": "appendiceal_orifice_image_reference",
                        "value": "image_reference_documented",
                    },
                    {
                        "classification": "ileocecal_valve_image_reference",
                        "value": "image_reference_documented",
                    },
                ],
            },
            {
                "finding": "colonoscopy_technical_quality",
                "classifications": [
                    {
                        "classification": "hd_videoendoscope_used",
                        "value": "yes",
                    },
                    {
                        "classification": "co2_insufflation_used",
                        "value": "yes",
                    },
                ],
            },
            {
                "finding": "colonoscopy_complication_status",
                "classifications": [
                    {
                        "classification": "colonoscopy_complication_occurred",
                        "value": "documented_none",
                    }
                ],
            },
            {
                "finding": "colonoscopy_pathology_summary",
                "classifications": [
                    {
                        "classification": "colonoscopy_pathology_status",
                        "value": "documented_none",
                    }
                ],
            },
            {
                "finding": "colonoscopy_follow_up_plan",
                "classifications": [
                    {
                        "classification": "colonoscopy_follow_up_recommendation",
                        "value": "recommendation_no_follow_up",
                    }
                ],
            },
        ],
        examination="colonoscopy",
        indications_payload=[{"indication": "colonoscopy_screening"}],
        examiners=["examiner-1"],
    )

    validation = kb.evaluate_report_template_validators(
        "colonoscopy_training_basic",
        p_examination=p_examination,
    )
    coverage = build_report_concept_coverage(
        kb=kb,
        requested_template_name="colonoscopy_training_basic",
        template_export=kb.export_report_template("colonoscopy_training_basic"),
        p_examination=p_examination,
        validation=validation,
    )

    assert validation["ok"] is True, {
        key: [
            (result["name"], result.get("issues"))
            for result in validation[key]
            if result.get("ok") is False
        ]
        for key in (
            "findings_validators",
            "examination_validators",
            "classification_validators",
        )
    }
    assert {item.validation_status for item in coverage.concepts} == {"present"}
    assert len(coverage.concepts) == 34
    cited_concepts = {
        item.concept_id: item.guideline_citations
        for item in coverage.concepts
        if item.guideline_citations
    }
    assert cited_concepts["koloskopie.indikation"] == (
        "AWMF-021-022 Statement 2.36: Indikation",
    )
    assert cited_concepts["koloskopie.monitoring.sauerstoffsaettigung"] == (
        "AWMF-021-014 Kapitel 5.4 und Empfehlung 5.10",
    )


def test_colonoscopy_conditional_quality_rules() -> None:
    loader = DataLoader(input_dirs=[DATA_ROOT])
    loader.load_module_configs()
    kb = loader.load_knowledge_base("report_template_examples")

    incomplete_rule = kb.findings_validator[
        "koloskopie_inkomplettheitsgrund_erforderlich"
    ]
    incomplete_without_reason = evaluate_findings_validator_runtime(
        incomplete_rule,
        reported_findings=[
            {
                "finding": "colonoscopy_deepest_viewed_location",
                "classifications": {
                    "colonoscopy_location_default": "sigmoid_colon",
                },
            }
        ],
    )
    complete_without_reason = evaluate_findings_validator_runtime(
        incomplete_rule,
        reported_findings=[
            {
                "finding": "colonoscopy_deepest_viewed_location",
                "classifications": {
                    "colonoscopy_location_default": "cecum",
                },
            }
        ],
    )
    incomplete_with_reason = evaluate_findings_validator_runtime(
        incomplete_rule,
        reported_findings=[
            {
                "finding": "colonoscopy_deepest_viewed_location",
                "classifications": {
                    "colonoscopy_location_default": "sigmoid_colon",
                    "colonoscopy_not_complete_reason": (
                        "colonoscopy_incomplete_stenosis"
                    ),
                },
            }
        ],
    )

    assert incomplete_without_reason["ok"] is False
    assert complete_without_reason["ok"] is True
    assert incomplete_with_reason["ok"] is True

    withdrawal_rule = kb.findings_validator[
        "koloskopie_rueckzugszeit_mindestens_sechs_minuten_oder_begruendet"
    ]
    too_short = evaluate_findings_validator_runtime(
        withdrawal_rule,
        reported_findings=[
            {
                "finding": "colonoscopy_withdrawal_time_minutes",
                "classifications": {"time_minutes_generic": 5},
            }
        ],
    )
    threshold_met = evaluate_findings_validator_runtime(
        withdrawal_rule,
        reported_findings=[
            {
                "finding": "colonoscopy_withdrawal_time_minutes",
                "classifications": {"time_minutes_generic": 6},
            }
        ],
    )

    assert too_short["ok"] is False
    assert threshold_met["ok"] is True

    repeat_rule = kb.findings_validator[
        "koloskopie_inadaequate_vorbereitung_fruehe_wiederholung"
    ]
    inadequate_without_plan = evaluate_findings_validator_runtime(
        repeat_rule,
        reported_findings=[
            {
                "finding": "bowel_preparation_bbps_total",
                "classifications": {
                    "bowel_prep_boston_total": "bbps_total_5",
                },
            }
        ],
    )
    inadequate_with_plan = evaluate_findings_validator_runtime(
        repeat_rule,
        reported_findings=[
            {
                "finding": "bowel_preparation_bbps_total",
                "classifications": {
                    "bowel_prep_boston_total": "bbps_total_5",
                },
            },
            {
                "finding": "colonoscopy_early_repeat_plan",
                "classifications": {
                    "colonoscopy_early_repeat_plan": "repeat_within_one_year",
                },
            },
        ],
    )

    assert inadequate_without_plan["ok"] is False
    assert inadequate_with_plan["ok"] is True

    medication_rule = kb.findings_validator[
        "koloskopie_medikationsgabe_wenn_verabreicht"
    ]
    medication_without_administration = evaluate_findings_validator_runtime(
        medication_rule,
        reported_findings=[
            {
                "finding": "endoscopy_medication_status",
                "classifications": {
                    "endoscopy_medication_documentation_status": ("documented_present"),
                },
            }
        ],
    )
    medication_with_administration = evaluate_findings_validator_runtime(
        medication_rule,
        reported_findings=[
            {
                "finding": "endoscopy_medication_status",
                "classifications": {
                    "endoscopy_medication_documentation_status": ("documented_present"),
                },
            },
            {
                "finding": "endoscopy_medication_administration",
                "classifications": {
                    "endoscopy_medication_product_and_dose": [
                        "medication_propofol",
                        120,
                    ],
                    "medication_administration_route": ("medication_route_intravenous"),
                    "medication_administration_method": "medication_method_bolus",
                },
            },
        ],
    )

    assert medication_without_administration["ok"] is False
    assert medication_with_administration["ok"] is True

    sedation_documentation_rule = kb.findings_validator[
        "koloskopie_sedierungsdokumentation_wenn_sediert"
    ]
    sedation_without_monitoring = evaluate_findings_validator_runtime(
        sedation_documentation_rule,
        reported_findings=[
            {
                "finding": "sedation_endoscopy",
                "classifications": {"sedation_performed": "yes"},
            }
        ],
    )
    sedation_with_documentation = evaluate_findings_validator_runtime(
        sedation_documentation_rule,
        reported_findings=[
            {
                "finding": "sedation_endoscopy",
                "classifications": {"sedation_performed": "yes"},
            },
            {"finding": "endoscopy_sedation_monitoring_measurement"},
            {"finding": "endoscopy_supplemental_oxygen_administration"},
            {"finding": "endoscopy_intravenous_fluid_status"},
            {"finding": "endoscopy_post_sedation_recovery_assessment"},
            {"finding": ("endoscopy_post_sedation_discharge_or_transfer_assessment")},
        ],
    )

    assert sedation_without_monitoring["ok"] is False
    assert sedation_with_documentation["ok"] is True

    asa_when_sedated_rule = kb.findings_validator["koloskopie_asa_wenn_sediert"]
    sedated_without_asa = evaluate_findings_validator_runtime(
        asa_when_sedated_rule,
        reported_findings=[
            {
                "finding": "sedation_endoscopy",
                "classifications": {"sedation_performed": "yes"},
            }
        ],
    )
    sedated_with_asa = evaluate_findings_validator_runtime(
        asa_when_sedated_rule,
        reported_findings=[
            {
                "finding": "sedation_endoscopy",
                "classifications": {"sedation_performed": "yes"},
            },
            {"finding": "endoscopy_preprocedure_asa_assessment"},
            {"finding": "endoscopy_preprocedure_physical_assessment"},
            {"finding": "endoscopy_preprocedure_last_oral_intake"},
        ],
    )

    assert sedated_without_asa["ok"] is False
    assert sedated_with_asa["ok"] is True

    fluid_rule = kb.findings_validator[
        "koloskopie_intravenoese_fluessigkeitsgabe_wenn_verabreicht"
    ]
    fluid_without_administration = evaluate_findings_validator_runtime(
        fluid_rule,
        reported_findings=[
            {
                "finding": "endoscopy_intravenous_fluid_status",
                "classifications": {
                    "intravenous_fluid_documentation_status": "documented_present"
                },
            }
        ],
    )
    fluid_with_administration = evaluate_findings_validator_runtime(
        fluid_rule,
        reported_findings=[
            {
                "finding": "endoscopy_intravenous_fluid_status",
                "classifications": {
                    "intravenous_fluid_documentation_status": "documented_present"
                },
            },
            {"finding": "endoscopy_intravenous_fluid_administration"},
        ],
    )

    assert fluid_without_administration["ok"] is False
    assert fluid_with_administration["ok"] is True

    dose_rule = kb.classification_validator[
        "koloskopie_medikament_und_dosis_vollstaendig"
    ]
    dose_rule_kwargs = {
        "classifications": kb.classification,
        "classification_choices": kb.classification_choice,
        "classification_choice_descriptors": kb.classification_choice_descriptor,
    }
    absent_administration = evaluate_classification_validator_runtime(
        dose_rule,
        **dose_rule_kwargs,
        reported_findings=[],
    )
    product_without_dose = evaluate_classification_validator_runtime(
        dose_rule,
        **dose_rule_kwargs,
        reported_findings=[
            {
                "finding": "endoscopy_medication_administration",
                "classifications": {
                    "endoscopy_medication_product_and_dose": "medication_propofol"
                },
            }
        ],
    )
    product_with_dose = evaluate_classification_validator_runtime(
        dose_rule,
        **dose_rule_kwargs,
        reported_findings=[
            {
                "finding": "endoscopy_medication_administration",
                "classifications": {
                    "endoscopy_medication_product_and_dose": [
                        "medication_propofol",
                        120,
                    ]
                },
            }
        ],
    )

    assert absent_administration["ok"] is True
    assert product_without_dose["ok"] is False
    assert product_without_dose["issues"][0]["code"] == (
        "classification_value_not_present"
    )
    assert product_with_dose["ok"] is True

    administration_time_rule = kb.classification_validator[
        "koloskopie_medikament_zeitpunkt_vollstaendig"
    ]
    time_without_value = evaluate_classification_validator_runtime(
        administration_time_rule,
        **dose_rule_kwargs,
        reported_findings=[
            {
                "finding": "endoscopy_medication_administration",
                "classifications": {
                    "medication_administration_time": (
                        "medication_administration_time_recorded"
                    )
                },
            }
        ],
    )
    time_with_value = evaluate_classification_validator_runtime(
        administration_time_rule,
        **dose_rule_kwargs,
        reported_findings=[
            {
                "finding": "endoscopy_medication_administration",
                "classifications": {
                    "medication_administration_time": [
                        "medication_administration_time_recorded",
                        "10:30",
                    ]
                },
            }
        ],
    )

    assert time_without_value["ok"] is False
    assert time_with_value["ok"] is True

    administration_method_rule = kb.classification_validator[
        "koloskopie_medikament_verabreichungsform_vollstaendig"
    ]
    infusion_without_flow_rate = evaluate_classification_validator_runtime(
        administration_method_rule,
        **dose_rule_kwargs,
        reported_findings=[
            {
                "finding": "endoscopy_medication_administration",
                "classifications": {
                    "medication_administration_method": "medication_method_infusion"
                },
            }
        ],
    )
    infusion_with_flow_rate = evaluate_classification_validator_runtime(
        administration_method_rule,
        **dose_rule_kwargs,
        reported_findings=[
            {
                "finding": "endoscopy_medication_administration",
                "classifications": {
                    "medication_administration_method": [
                        "medication_method_infusion",
                        25,
                    ]
                },
            }
        ],
    )

    assert infusion_without_flow_rate["ok"] is False
    assert infusion_with_flow_rate["ok"] is True

    room_entry_rule = kb.classification_validator[
        "koloskopie_prozesszeit_raum_betreten_vollstaendig"
    ]
    room_entry_without_timestamp = evaluate_classification_validator_runtime(
        room_entry_rule,
        **dose_rule_kwargs,
        reported_findings=[
            {
                "finding": "endoscopy_process_timestamps",
                "classifications": {
                    "endoscopy_room_entry_time": ("endoscopy_room_entry_time_recorded")
                },
            }
        ],
    )
    room_entry_with_timestamp = evaluate_classification_validator_runtime(
        room_entry_rule,
        **dose_rule_kwargs,
        reported_findings=[
            {
                "finding": "endoscopy_process_timestamps",
                "classifications": {
                    "endoscopy_room_entry_time": [
                        "endoscopy_room_entry_time_recorded",
                        "10:00",
                    ]
                },
            }
        ],
    )

    assert room_entry_without_timestamp["ok"] is False
    assert room_entry_with_timestamp["ok"] is True

    team_timeout_time_rule = kb.classification_validator[
        "koloskopie_team_timeout_zeitpunkt_vollstaendig"
    ]
    team_timeout_without_timestamp = evaluate_classification_validator_runtime(
        team_timeout_time_rule,
        **dose_rule_kwargs,
        reported_findings=[
            {
                "finding": "endoscopy_preprocedure_team_timeout",
                "classifications": {
                    "endoscopy_team_timeout_time": (
                        "endoscopy_team_timeout_time_recorded"
                    )
                },
            }
        ],
    )
    team_timeout_with_timestamp = evaluate_classification_validator_runtime(
        team_timeout_time_rule,
        **dose_rule_kwargs,
        reported_findings=[
            {
                "finding": "endoscopy_preprocedure_team_timeout",
                "classifications": {
                    "endoscopy_team_timeout_time": [
                        "endoscopy_team_timeout_time_recorded",
                        "10:05",
                    ]
                },
            }
        ],
    )

    assert team_timeout_without_timestamp["ok"] is False
    assert team_timeout_with_timestamp["ok"] is True

    identity_documentation_rule = kb.classification_validator[
        "koloskopie_team_timeout_patientenidentitaet_vollstaendig"
    ]
    documented_negative_identity_check = evaluate_classification_validator_runtime(
        identity_documentation_rule,
        **dose_rule_kwargs,
        reported_findings=[
            {
                "finding": "endoscopy_preprocedure_team_timeout",
                "classifications": {
                    "patient_identity_confirmation_status": (
                        "patient_identity_not_confirmed"
                    )
                },
            }
        ],
    )

    assert documented_negative_identity_check["ok"] is True


def test_large_polyp_requires_resection_retrieval_and_histology_status() -> None:
    loader = DataLoader(input_dirs=[DATA_ROOT])
    loader.load_module_configs()
    kb = loader.load_knowledge_base("report_template_examples")
    rule = kb.findings_validator["koloskopie_polyp_groesser_fuenf_mm_qualitaetsdaten"]

    incomplete = evaluate_findings_validator_runtime(
        rule,
        reported_findings=[
            {
                "finding": "colon_polyp",
                "classifications": {
                    "lesion_size_mm": 8,
                    "colon_lesion_paris": "colon_lesion_paris_0_is",
                },
            }
        ],
    )
    complete = evaluate_findings_validator_runtime(
        rule,
        reported_findings=[
            {
                "finding": "colon_polyp",
                "classifications": {
                    "lesion_size_mm": 8,
                    "colon_lesion_paris": "colon_lesion_paris_0_is",
                    "colonoscopy_specimen_retrieval_status": "specimen_retrieved",
                    "colonoscopy_histology_submission_status": "histology_submitted",
                    "colonoscopy_resection_technique_status": (
                        "resection_technique_documented"
                    ),
                },
            }
        ],
    )

    assert incomplete["ok"] is False
    assert complete["ok"] is True


def test_knowledge_base_runtime_execution_flags_missing_exam_requirement() -> None:
    loader = DataLoader(input_dirs=[DATA_ROOT])
    loader.load_module_configs()
    kb = loader.load_knowledge_base("report_template_examples")

    result = kb.evaluate_report_template_validators(
        "star_upper_gi_main",
        p_examination=_build_p_examination(
            [
                {
                    "finding": "esophagus_polyp",
                    "classifications": [
                        {"classification": "size_mm", "value": 8},
                    ],
                }
            ]
        ),
    )

    assert result["ok"] is False
    exam_results = result["examination_validators"]
    assert exam_results
    assert exam_results[0]["ok"] is False


def test_knowledge_base_runtime_rejects_finding_for_wrong_examination() -> None:
    loader = DataLoader(input_dirs=[DATA_ROOT])
    loader.load_module_configs()
    kb = loader.load_knowledge_base("report_template_examples")

    p_examination = _build_p_examination(
        [
            {
                "finding": "esophagus_polyp",
                "classifications": [],
            }
        ],
        examination="colonoscopy",
    )

    try:
        kb.evaluate_report_template_validators(
            "star_upper_gi_main",
            p_examination=p_examination,
        )
    except SemanticAdmissibilityError as exc:
        assert "does not match report template" in str(exc)
    else:
        raise AssertionError("Expected semantic admissibility failure")


def test_knowledge_base_admissibility_rejects_forbidden_finding_in_examination() -> (
    None
):
    loader = DataLoader(input_dirs=[DATA_ROOT])
    loader.load_module_configs()
    kb = loader.load_knowledge_base("report_template_examples")

    p_examination = _build_p_examination(
        [
            {
                "finding": "esophagus_polyp",
                "classifications": [],
            }
        ],
        examination="colonoscopy",
    )

    try:
        kb.assert_examination_admissibility(p_examination)
    except SemanticAdmissibilityError as exc:
        assert "not permitted for examination" in str(exc)
    else:
        raise AssertionError("Expected semantic admissibility failure")


def test_knowledge_base_admissibility_rejects_smuggled_classification() -> None:
    loader = DataLoader(input_dirs=[DATA_ROOT])
    loader.load_module_configs()
    kb = loader.load_knowledge_base("report_template_examples")

    p_examination = _build_p_examination(
        [
            {
                "finding": "star_upper_gi_mucosa_esophagus_abnormal",
                "classifications": [
                    {"classification": "size_mm", "value": 8},
                ],
            }
        ]
    )

    try:
        kb.evaluate_report_template_validators(
            "star_upper_gi_main",
            p_examination=p_examination,
        )
    except SemanticAdmissibilityError as exc:
        assert "size_mm" in str(exc)
        assert "not permitted for finding" in str(
            exc
        ) or "Unknown classification" in str(exc)
    else:
        raise AssertionError("Expected semantic admissibility failure")


def test_knowledge_base_admissibility_rejects_hallucinated_intervention() -> None:
    loader = DataLoader(input_dirs=[DATA_ROOT])
    loader.load_module_configs()
    kb = loader.load_knowledge_base("report_template_examples")

    p_examination = _build_p_examination(
        [
            {
                "finding": "star_upper_gi_mucosa_esophagus_abnormal",
                "classifications": [],
            }
        ]
    )
    p_finding = p_examination.patient_findings[0]
    p_interventions = PFindingInterventions.model_validate(
        {
            "patient_finding": str(p_finding.uuid),
            "patient_finding_interventions": [],
        }
    )
    p_interventions.patient_finding_interventions.append(
        PFindingIntervention.model_validate(
            {
                "patient_finding_interventions": str(p_interventions.uuid),
                "intervention": "endoscopy_hemoclip_generic",
            }
        )
    )
    p_finding.patient_finding_interventions.append(p_interventions)

    try:
        kb.evaluate_report_template_validators(
            "star_upper_gi_main",
            p_examination=p_examination,
        )
    except SemanticAdmissibilityError as exc:
        assert "endoscopy_hemoclip_generic" in str(exc)
        assert "not permitted for finding" in str(exc) or "Unknown intervention" in str(
            exc
        )
    else:
        raise AssertionError("Expected semantic admissibility failure")


def test_knowledge_base_admissibility_rejects_smuggled_indication_classification() -> (
    None
):
    loader = DataLoader(input_dirs=[DATA_ROOT])
    loader.load_module_configs()
    kb = loader.load_knowledge_base("lx_examinations")

    p_examination = _build_p_examination(
        [],
        examination="colonoscopy",
        indications_payload=[
            {
                "indication": "colonoscopy_screening",
                "classifications": [{"classification": "size_mm", "value": 8}],
            }
        ],
    )

    try:
        kb.assert_examination_admissibility(p_examination)
    except SemanticAdmissibilityError as exc:
        assert "size_mm" in str(exc)
        assert "permitted for indication" in str(
            exc
        ) or "Unknown indication classification" in str(exc)
    else:
        raise AssertionError("Expected semantic admissibility failure")


def test_knowledge_base_admissibility_rejects_unknown_examination() -> None:
    loader = DataLoader(input_dirs=[DATA_ROOT])
    loader.load_module_configs()
    kb = loader.load_knowledge_base("report_template_examples")

    p_examination = _build_p_examination([], examination="made_up_examination_type")

    try:
        kb.assert_examination_admissibility(p_examination)
    except SemanticAdmissibilityError as exc:
        assert "Unknown examination" in str(exc)
    else:
        raise AssertionError("Expected semantic admissibility failure")


def test_upper_gi_quality_2025_emits_authoritative_concept_coverage() -> None:
    loader = DataLoader(input_dirs=[DATA_ROOT])
    loader.load_module_configs()
    kb = loader.load_knowledge_base("report_template_examples")
    p_examination = _build_p_examination(
        [
            {
                "finding": finding_name,
                "classifications": [
                    {"classification": "yes_no_unknown_classification", "value": "no"}
                ],
            }
            for finding_name in (
                "star_upper_gi_mucosa_esophagus_abnormal",
                "star_upper_gi_mucosa_stomach_abnormal",
                "star_upper_gi_mucosa_duodenum_abnormal",
            )
        ]
        + [
            {
                "finding": finding_name,
                "classifications": [
                    {
                        "classification": "distance_cm",
                        "classification_choice": "distance_cm",
                        "descriptor": "length_cm_descriptor",
                        "descriptor_value": distance,
                    }
                ],
            }
            for finding_name, distance in (
                ("star_upper_gi_location_esophagogastric_junction", 40),
                ("star_upper_gi_location_hiatus", 41),
                ("star_upper_gi_location_squamocolumnar_junction", 40),
            )
        ]
        + [
            {
                "finding": "star_upper_gi_imaging_modality_esophagus",
                "classifications": [
                    {
                        "classification": (
                            "upper_gi_esophagus_imaging_modality_classification"
                        ),
                        "value": "star_upper_gi_imaging_modality_white_light",
                    }
                ],
            }
        ],
        examination="star_upper_gi_endoscopy",
    )

    validation = kb.evaluate_report_template_validators(
        "upper_gi_quality_2025",
        p_examination=p_examination,
    )
    coverage = build_report_concept_coverage(
        kb=kb,
        requested_template_name="upper_gi_quality_2025",
        template_export=kb.export_report_template("upper_gi_quality_2025"),
        p_examination=p_examination,
        validation=validation,
    )

    assert validation["ok"] is True
    assert len(coverage.concepts) == 7
    assert {item.validation_status for item in coverage.concepts} == {"present"}
    assert all(item.guideline_citations for item in coverage.concepts)


@pytest.mark.parametrize(
    ("template_name", "examination", "finding_values"),
    [
        (
            "ercp_quality_2018",
            "ercp",
            [
                (
                    "ercp_antibiotic_prophylaxis",
                    "ercp_antibiotic_prophylaxis_status",
                    "quality_adequate",
                ),
                (
                    "ercp_bile_duct_cannulation",
                    "ercp_bile_duct_cannulation_outcome",
                    "quality_successful",
                ),
                (
                    "ercp_biliary_stent_placement",
                    "ercp_biliary_stent_placement_outcome",
                    "quality_not_applicable",
                ),
                (
                    "ercp_bile_duct_stone_extraction",
                    "ercp_bile_duct_stone_extraction_outcome",
                    "quality_not_applicable",
                ),
                (
                    "ercp_post_ercp_pancreatitis",
                    "ercp_post_ercp_pancreatitis_status",
                    "quality_absent",
                ),
            ],
        ),
        (
            "eus_quality_2025",
            "endoscopic_ultrasound",
            [
                (
                    "eus_informed_consent",
                    "eus_informed_consent_status",
                    "quality_obtained",
                ),
                (
                    "eus_landmark_documentation",
                    "eus_landmark_documentation_status",
                    "quality_complete",
                ),
                (
                    "eus_pancreatic_cyst_description",
                    "eus_pancreatic_cyst_description_status",
                    "quality_not_applicable",
                ),
                (
                    "eus_tissue_acquisition",
                    "eus_tissue_acquisition_result",
                    "quality_not_applicable",
                ),
                ("eus_adverse_events", "eus_adverse_event_status", "quality_absent"),
            ],
        ),
    ],
)
def test_advanced_endoscopy_templates_emit_authoritative_concept_coverage(
    template_name: str,
    examination: str,
    finding_values: list[tuple[str, str, str]],
) -> None:
    loader = DataLoader(input_dirs=[DATA_ROOT])
    loader.load_module_configs()
    kb = loader.load_knowledge_base("report_template_examples")
    p_examination = _build_p_examination(
        [
            {
                "finding": finding_name,
                "classifications": [
                    {"classification": classification_name, "value": value}
                ],
            }
            for finding_name, classification_name, value in finding_values
        ],
        examination=examination,
    )

    validation = kb.evaluate_report_template_validators(
        template_name,
        p_examination=p_examination,
    )
    coverage = build_report_concept_coverage(
        kb=kb,
        requested_template_name=template_name,
        template_export=kb.export_report_template(template_name),
        p_examination=p_examination,
        validation=validation,
    )

    assert validation["ok"] is True
    assert len(coverage.concepts) == 5
    assert {item.validation_status for item in coverage.concepts} == {"present"}
    assert all(item.guideline_citations for item in coverage.concepts)
