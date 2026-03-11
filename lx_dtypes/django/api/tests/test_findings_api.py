import json
from datetime import date
from importlib import import_module

import pytest
from django.conf import settings
from django.test import Client

try:
    host_models_module = getattr(settings, "LX_DTYPES_HOST_MODELS_MODULE", None)
    if not host_models_module:
        raise ModuleNotFoundError
    host_models = import_module(host_models_module)
    Center = host_models.Center
    Examination = host_models.Examination
    Finding = host_models.Finding
    FindingClassification = host_models.FindingClassification
    FindingClassificationChoice = host_models.FindingClassificationChoice
    Gender = host_models.Gender
    Patient = host_models.Patient
    PatientExamination = host_models.PatientExamination
except (ModuleNotFoundError, RuntimeError, AttributeError):  # pragma: no cover
    pytest.skip(
        "Host application models are required for lx_dtypes Django API integration tests.",
        allow_module_level=True,
    )

pytestmark = pytest.mark.django_db


def _create_patient_examination(examination: Examination) -> PatientExamination:
    gender, _ = Gender.objects.get_or_create(name="male")
    center, _ = Center.objects.get_or_create(name="Test Center")
    patient = Patient.objects.create(
        first_name="Base",
        last_name="Api",
        dob=date(1980, 1, 1),
        gender=gender,
        center=center,
    )
    return PatientExamination.objects.create(
        patient=patient,
        examination=examination,
        hash=f"pe-{patient.id}-{examination.id}",
    )


def _create_exam_graph() -> tuple[
    Examination,
    Finding,
    FindingClassification,
    FindingClassificationChoice,
]:
    examination = Examination.objects.create(name="colonoscopy")
    finding = Finding.objects.create(name="colon_polyp")
    examination.findings.add(finding)
    classification = FindingClassification.objects.create(
        name="size_classification",
        description="Size category",
    )
    choice_small = FindingClassificationChoice.objects.create(
        name="small_polyp",
        description="small",
        subcategories={},
        numerical_descriptors={},
    )
    classification.choices.add(choice_small)
    finding.finding_classifications.add(classification)
    return examination, finding, classification, choice_small


def test_base_api_findings_read_endpoints_shape() -> None:
    client = Client()
    examination, finding, classification, choice = _create_exam_graph()

    findings_res = client.get(
        f"/base_api/examinations/{examination.id}/findings/",
        secure=True,
    )
    assert findings_res.status_code == 200, findings_res.content.decode()
    findings_payload = findings_res.json()
    assert isinstance(findings_payload, list)
    assert findings_payload
    first_finding = findings_payload[0]
    assert first_finding["id"] == finding.id
    assert "classifications" in first_finding

    classifications_res = client.get(
        f"/base_api/findings/{finding.id}/classifications/",
        secure=True,
    )
    assert classifications_res.status_code == 200
    classifications_payload = classifications_res.json()
    assert isinstance(classifications_payload, list)
    assert classifications_payload[0]["id"] == classification.id
    assert isinstance(classifications_payload[0].get("choices"), list)

    choices_res = client.get(
        f"/base_api/classifications/{classification.id}/choices/",
        secure=True,
    )
    assert choices_res.status_code == 200
    choices_payload = choices_res.json()
    assert "choices" in choices_payload
    assert choices_payload["choices"][0]["id"] == choice.id


def test_base_api_patient_findings_crud_and_classifications() -> None:
    client = Client()
    examination, finding, classification, choice = _create_exam_graph()
    patient_examination = _create_patient_examination(examination)

    create_res = client.post(
        "/base_api/patient-findings/",
        data=json.dumps(
            {
                "patient_examination": patient_examination.id,
                "finding": finding.id,
                "classifications": [
                    {"classification": classification.id, "choice": choice.id}
                ],
            }
        ),
        content_type="application/json",
        secure=True,
    )
    assert create_res.status_code == 200, create_res.content.decode()
    created_payload = create_res.json()
    assert created_payload["patient_examination"] == patient_examination.id
    assert created_payload["finding"] == finding.id
    patient_finding_id = created_payload["id"]

    list_res = client.get(
        f"/base_api/patient-findings/?patient_examination={patient_examination.id}",
        secure=True,
    )
    assert list_res.status_code == 200
    listed = list_res.json()
    assert isinstance(listed, list)
    assert len(listed) == 1
    assert listed[0]["id"] == patient_finding_id
    assert len(listed[0]["classifications"]) == 1

    set_classifications_res = client.post(
        f"/base_api/patient-findings/{patient_finding_id}/classifications/",
        data=json.dumps(
            {
                "replace": True,
                "classifications": [
                    {"classification": classification.id, "choice": choice.id}
                ],
            }
        ),
        content_type="application/json",
        secure=True,
    )
    assert set_classifications_res.status_code == 200
    assert len(set_classifications_res.json()["classifications"]) == 1

    patch_res = client.patch(
        f"/base_api/patient-findings/{patient_finding_id}/",
        data=json.dumps({"is_active": True}),
        content_type="application/json",
        secure=True,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["id"] == patient_finding_id

    delete_res = client.delete(
        f"/base_api/patient-findings/{patient_finding_id}/",
        secure=True,
    )
    assert delete_res.status_code == 200
    assert delete_res.json()["success"] is True

    list_after_delete = client.get(
        f"/base_api/patient-findings/?patient_examination={patient_examination.id}",
        secure=True,
    )
    assert list_after_delete.status_code == 200
    assert list_after_delete.json() == []


def test_base_api_patient_findings_validation_invalid_choice() -> None:
    client = Client()
    examination, finding, classification, _choice = _create_exam_graph()
    patient_examination = _create_patient_examination(examination)

    invalid_choice = FindingClassificationChoice.objects.create(
        name="invalid_for_classification",
        description="invalid",
        subcategories={},
        numerical_descriptors={},
    )

    create_res = client.post(
        "/base_api/patient-findings/",
        data=json.dumps(
            {
                "patient_examination": patient_examination.id,
                "finding": finding.id,
                "classifications": [
                    {
                        "classification": classification.id,
                        "choice": invalid_choice.id,
                    }
                ],
            }
        ),
        content_type="application/json",
        secure=True,
    )
    assert create_res.status_code == 400, create_res.content.decode()
    payload = create_res.json()
    assert payload.get("code") == "invalid-choice"


def test_base_api_patient_findings_validation_duplicate_finding() -> None:
    client = Client()
    examination, finding, _classification, _choice = _create_exam_graph()
    patient_examination = _create_patient_examination(examination)

    first_res = client.post(
        "/base_api/patient-findings/",
        data=json.dumps(
            {
                "patient_examination": patient_examination.id,
                "finding": finding.id,
                "classifications": [],
            }
        ),
        content_type="application/json",
        secure=True,
    )
    assert first_res.status_code == 200, first_res.content.decode()

    duplicate_res = client.post(
        "/base_api/patient-findings/",
        data=json.dumps(
            {
                "patient_examination": patient_examination.id,
                "finding": finding.id,
                "classifications": [],
            }
        ),
        content_type="application/json",
        secure=True,
    )
    assert duplicate_res.status_code == 400
    payload = duplicate_res.json()
    assert payload.get("code") == "duplicate-finding"


def test_base_api_patient_findings_validation_invalid_finding_for_examination() -> None:
    client = Client()
    examination, _finding, _classification, _choice = _create_exam_graph()
    patient_examination = _create_patient_examination(examination)
    unrelated_finding = Finding.objects.create(name="unrelated_finding")

    create_res = client.post(
        "/base_api/patient-findings/",
        data=json.dumps(
            {
                "patient_examination": patient_examination.id,
                "finding": unrelated_finding.id,
                "classifications": [],
            }
        ),
        content_type="application/json",
        secure=True,
    )
    assert create_res.status_code == 400
    payload = create_res.json()
    assert payload.get("code") == "invalid-finding"
