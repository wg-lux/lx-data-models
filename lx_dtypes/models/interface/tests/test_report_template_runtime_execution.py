from pathlib import Path

from lx_dtypes.models.interface.DataLoader import DataLoader
from lx_dtypes.models.interface.KnowledgeBase import SemanticAdmissibilityError
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
from lx_dtypes.models.ledger.p_intervention.Pydantic import PFindingIntervention
from lx_dtypes.models.ledger.p_interventions.Pydantic import PFindingInterventions


DATA_ROOT = Path(__file__).resolve().parents[3] / "data"


def _build_p_examination(
    findings_payload: list[dict[str, object]],
    *,
    examination: str = "star_upper_gi_endoscopy",
) -> PExamination:
    p_examination = PExamination.model_validate(
        {
            "patient": "test_patient",
            "examination": examination,
            "patient_findings": [],
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
                if not isinstance(raw_value, str):
                    p_choice.patient_finding_classification_choice_descriptors.append(
                        PFindingClassificationChoiceDescriptor.model_validate(
                            {
                                "descriptor_value": raw_value,
                                "classification_choice_descriptor": "length_mm_descriptor",
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
