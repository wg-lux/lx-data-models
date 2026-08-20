import json
from datetime import date
from importlib import import_module
from typing import Any

import pytest
from django.contrib.auth import get_user_model
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
    Indication = host_models.Indication
    Patient = host_models.Patient
    PatientExamination = host_models.PatientExamination
except (ModuleNotFoundError, RuntimeError, AttributeError):  # pragma: no cover
    pytest.skip(
        "Host application models are required for lx_dtypes Django API integration tests.",
        allow_module_level=True,
    )

from lx_dtypes.django.api import findings_routes, terminology_routes

pytestmark = pytest.mark.django_db


def _create_patient_examination(examination: Any) -> Any:
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


def _create_exam_graph() -> tuple[Any, Any, Any, Any]:
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


def _mock_kb_lookup(module_name: str, version: str | None = None) -> dict[str, Any]:
    if module_name != "catalog_module":
        return {
            "examination": {},
            "finding": {},
            "classification": {},
            "classification_choice": {},
            "indication": {},
        }
    normalized_version = str(version or "").strip()
    if normalized_version == "1.0.0":
        return {
            "examination": {
                "colonoscopy": {
                    "name": "colonoscopy",
                    "findings": ["colon_polyp"],
                    "indications": ["screening"],
                }
            },
            "finding": {
                "colon_polyp": {
                    "name": "colon_polyp",
                    "classifications": ["size_classification"],
                }
            },
            "classification": {
                "size_classification": {
                    "name": "size_classification",
                    "classification_choices": ["small_polyp"],
                }
            },
            "classification_choice": {
                "small_polyp": {"name": "small_polyp"},
            },
            "indication": {
                "screening": {"name": "screening"},
            },
        }
    if normalized_version == "2.0.0":
        return {
            "examination": {
                "colonoscopy": {
                    "name": "colonoscopy",
                    "findings": [],
                    "indications": [],
                }
            },
            "finding": {},
            "classification": {},
            "classification_choice": {},
            "indication": {},
        }
    return {
        "examination": {},
        "finding": {},
        "classification": {},
        "classification_choice": {},
        "indication": {},
    }


def _create_exam_graph_with_indication() -> tuple[Any, Any, Any, Any, Any]:
    examination = Examination.objects.create(
        name="colonoscopy",
        name_de="Koloskopie",
        name_en="Colonoscopy",
    )
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
    indication = Indication.objects.create(
        name="screening",
        name_de="Vorsorge",
        name_en="Screening",
    )
    examination.indications.add(indication)
    return examination, finding, classification, choice_small, indication


def test_base_api_findings_read_endpoints_shape() -> None:
    client = Client()
    examination, finding, classification, choice, indication = (
        _create_exam_graph_with_indication()
    )

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

    indications_res = client.get(
        f"/base_api/examinations/{examination.id}/indications/",
        secure=True,
    )
    assert indications_res.status_code == 200
    indications_payload = indications_res.json()
    assert isinstance(indications_payload, list)
    assert indications_payload[0]["name"] == "screening"
    assert indications_payload[0]["name_de"] == "Vorsorge"
    assert indications_payload[0]["name_en"] == "Screening"

    indications_tree_res = client.get(
        "/base_api/indications/tree/",
        secure=True,
    )
    assert indications_tree_res.status_code == 200
    indications_tree_payload = indications_tree_res.json()
    assert isinstance(indications_tree_payload, list)
    tree_screening = next(
        (item for item in indications_tree_payload if item["name"] == "screening"), None
    )
    assert tree_screening is not None
    assert tree_screening["name_de"] == "Vorsorge"
    assert tree_screening["name_en"] == "Screening"
    assert any(
        examination_entry["id"] == examination.id
        for examination_entry in tree_screening.get("examinations", [])
    )
    tree_examination = tree_screening["examinations"][0]
    assert tree_examination["name_de"] == "Koloskopie"
    assert tree_examination["name_en"] == "Colonoscopy"


def test_base_api_findings_read_endpoints_support_module_version_overrides(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Client()
    examination, finding, classification, choice, indication = (
        _create_exam_graph_with_indication()
    )
    monkeypatch.setattr(findings_routes, "_kb_lookup", _mock_kb_lookup)

    legacy_findings = client.get(
        f"/base_api/examinations/{examination.id}/findings/?module_name=catalog_module&module_version=1.0.0",
        secure=True,
    )
    assert legacy_findings.status_code == 200
    assert len(legacy_findings.json()) == 1
    assert legacy_findings.json()[0]["id"] == finding.id

    modern_findings = client.get(
        f"/base_api/examinations/{examination.id}/findings/?module_name=catalog_module&module_version=2.0.0",
        secure=True,
    )
    assert modern_findings.status_code == 200
    assert modern_findings.json() == []

    legacy_classifications = client.get(
        f"/base_api/findings/{finding.id}/classifications/?module_name=catalog_module&module_version=1.0.0",
        secure=True,
    )
    assert legacy_classifications.status_code == 200
    assert any(
        item["name"] == classification.name for item in legacy_classifications.json()
    )

    modern_classifications = client.get(
        f"/base_api/findings/{finding.id}/classifications/?module_name=catalog_module&module_version=2.0.0",
        secure=True,
    )
    assert modern_classifications.status_code == 200
    assert modern_classifications.json() == []

    legacy_choices = client.get(
        f"/base_api/classifications/{classification.id}/choices/?module_name=catalog_module&module_version=1.0.0",
        secure=True,
    )
    assert legacy_choices.status_code == 200
    assert legacy_choices.json()["choices"][0]["id"] == choice.id

    modern_choices = client.get(
        f"/base_api/classifications/{classification.id}/choices/?module_name=catalog_module&module_version=2.0.0",
        secure=True,
    )
    assert modern_choices.status_code == 200
    assert modern_choices.json() == {"choices": []}

    legacy_indications = client.get(
        f"/base_api/examinations/{examination.id}/indications/?module_name=catalog_module&module_version=1.0.0",
        secure=True,
    )
    assert legacy_indications.status_code == 200
    assert len(legacy_indications.json()) == 1
    assert legacy_indications.json()[0]["id"] == indication.id

    modern_indications = client.get(
        f"/base_api/examinations/{examination.id}/indications/?module_name=catalog_module&module_version=2.0.0",
        secure=True,
    )
    assert modern_indications.status_code == 200
    assert modern_indications.json() == []

    legacy_tree = client.get(
        "/base_api/indications/tree/?module_name=catalog_module&module_version=1.0.0",
        secure=True,
    )
    assert legacy_tree.status_code == 200
    legacy_tree_payload = legacy_tree.json()
    assert isinstance(legacy_tree_payload, list)
    assert any(node["name"] == indication.name for node in legacy_tree_payload)
    legacy_screening_node = next(
        node for node in legacy_tree_payload if node["name"] == indication.name
    )
    assert any(
        examination_entry["id"] == examination.id
        for examination_entry in legacy_screening_node.get("examinations", [])
    )

    modern_tree = client.get(
        "/base_api/indications/tree/?module_name=catalog_module&module_version=2.0.0",
        secure=True,
    )
    assert modern_tree.status_code == 200
    assert modern_tree.json() == []


def test_base_api_findings_read_routes_use_patient_examination_kb_when_requested(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Client()
    examination, _, _, _ = _create_exam_graph()
    patient_examination = _create_patient_examination(examination)
    patient_examination.knowledge_base_module = "catalog_module"
    patient_examination.knowledge_base_version = "1.0.0"
    patient_examination.save(
        update_fields=["knowledge_base_module", "knowledge_base_version"]
    )

    monkeypatch.setattr(
        terminology_routes,
        "active_terminology_selection",
        lambda: ("catalog_module", "2.0.0"),
    )
    monkeypatch.setattr(findings_routes, "_kb_lookup", _mock_kb_lookup)

    response = client.get(
        f"/base_api/examinations/{examination.id}/findings/?patient_examination_id={patient_examination.id}",
        secure=True,
    )
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_base_api_findings_read_routes_reject_unpinned_patient_examination(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Client()
    examination, _, _, _ = _create_exam_graph()
    patient_examination = _create_patient_examination(examination)
    patient_examination.knowledge_base_module = ""
    patient_examination.knowledge_base_version = ""
    patient_examination.save(
        update_fields=["knowledge_base_module", "knowledge_base_version"]
    )

    monkeypatch.setattr(
        terminology_routes,
        "active_terminology_selection",
        lambda: ("catalog_module", "2.0.0"),
    )
    monkeypatch.setattr(findings_routes, "_kb_lookup", _mock_kb_lookup)

    response = client.get(
        f"/base_api/examinations/{examination.id}/findings/?patient_examination_id={patient_examination.id}",
        secure=True,
    )
    assert response.status_code == 409
    assert response.json() == {
        "code": "knowledge-base-identity-required",
        "message": "PatientExamination requires an explicit knowledge-base identity.",
    }


def test_base_api_patient_examination_findings_read_uses_pinned_kb_when_examination_context_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Client()
    examination = Examination.objects.create(name="colonoscopy")
    finding_v1 = Finding.objects.create(name="POLYP-V1")
    finding_v2 = Finding.objects.create(name="POLYP-V2")
    examination.findings.add(finding_v1, finding_v2)

    patient_examination = _create_patient_examination(examination)
    patient_examination.knowledge_base_module = "catalog_module"
    patient_examination.knowledge_base_version = "1.0.0"
    patient_examination.save(
        update_fields=["knowledge_base_module", "knowledge_base_version"]
    )

    def _mock_catalog_kb_lookup(
        module_name: str, version: str | None = None
    ) -> dict[str, Any]:
        if module_name != "catalog_module":
            return {
                "examination": {},
                "finding": {},
                "classification": {},
                "classification_choice": {},
            }
        normalized_version = str(version or "").strip()
        if normalized_version == "1.0.0":
            return {
                "examination": {
                    "colonoscopy": {
                        "name": "colonoscopy",
                        "findings": ["POLYP-V1"],
                    }
                },
                "finding": {
                    "polyp-v1": {"name": "POLYP-V1", "classifications": []},
                },
                "classification": {},
                "classification_choice": {},
            }
        if normalized_version == "2.0.0":
            return {
                "examination": {
                    "colonoscopy": {
                        "name": "colonoscopy",
                        "findings": ["POLYP-V2"],
                    }
                },
                "finding": {
                    "polyp-v2": {"name": "POLYP-V2", "classifications": []},
                },
                "classification": {},
                "classification_choice": {},
            }
        return {
            "examination": {},
            "finding": {},
            "classification": {},
            "classification_choice": {},
        }

    monkeypatch.setattr(
        terminology_routes,
        "active_terminology_selection",
        lambda: ("catalog_module", "2.0.0"),
    )
    monkeypatch.setattr(findings_routes, "_kb_lookup", _mock_catalog_kb_lookup)

    response = client.get(
        f"/base_api/examinations/{examination.id}/findings/",
        secure=True,
    )

    assert response.status_code == 200, response.content.decode()
    payload = response.json()
    assert any(item["id"] == finding_v1.id for item in payload)
    assert not any(item["id"] == finding_v2.id for item in payload)


def test_base_api_patient_findings_uses_examination_pinned_kb_for_create_and_rejects_other_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Client()
    user_model = get_user_model()
    user = user_model.objects.create(
        username="legacy-kb-create",
        is_staff=True,
    )
    client.force_login(user)

    examination = Examination.objects.create(name="colonoscopy")
    finding_v1 = Finding.objects.create(name="POLYP-V1")
    finding_v2 = Finding.objects.create(name="POLYP-V2")
    examination.findings.add(finding_v1, finding_v2)
    patient_examination = _create_patient_examination(examination)
    patient_examination.knowledge_base_module = "catalog_module"
    patient_examination.knowledge_base_version = "1.0.0"
    patient_examination.save(
        update_fields=["knowledge_base_module", "knowledge_base_version"]
    )

    monkeypatch.setattr(
        findings_routes,
        "_kb_lookup",
        lambda _module_name, version=None: {
            "examination": {
                "colonoscopy": {
                    "name": "colonoscopy",
                    "findings": [
                        "POLYP-V1" if str(version or "") == "1.0.0" else "POLYP-V2"
                    ],
                }
            },
            "finding": {
                "polyp-v1": {"name": "POLYP-V1", "classifications": []},
                "polyp-v2": {"name": "POLYP-V2", "classifications": []},
            },
            "classification": {},
            "classification_choice": {},
        },
    )

    # active catalog is v2.0.0, but the exam is pinned to v1.0.0.
    monkeypatch.setattr(
        terminology_routes,
        "active_terminology_selection",
        lambda: ("catalog_module", "2.0.0"),
    )

    allowed_response = client.post(
        "/base_api/patient-findings/",
        data=json.dumps(
            {
                "patient_examination": patient_examination.id,
                "finding": finding_v1.id,
                "classifications": [],
            }
        ),
        content_type="application/json",
        secure=True,
    )
    assert allowed_response.status_code == 200, allowed_response.content.decode()

    blocked_response = client.post(
        "/base_api/patient-findings/",
        data=json.dumps(
            {
                "patient_examination": patient_examination.id,
                "finding": finding_v2.id,
                "classifications": [],
            }
        ),
        content_type="application/json",
        secure=True,
    )
    assert blocked_response.status_code == 400, blocked_response.content.decode()
    assert blocked_response.json().get("code") == "invalid-finding"


def test_base_api_patient_findings_create_fails_closed_when_access_check_callback_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Client()
    user_model = get_user_model()
    user = user_model.objects.create(
        username="missing-access-callback",
        is_staff=True,
    )
    client.force_login(user)
    examination, finding, _, _ = _create_exam_graph()
    patient_examination = _create_patient_examination(examination)

    monkeypatch.delattr(
        host_models, "patient_examination_access_allowed", raising=False
    )

    response = client.post(
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

    assert response.status_code == 404, response.content.decode()
    assert response.json().get("code") == "not-found"


def test_base_api_patient_findings_crud_and_classifications() -> None:
    client = Client()
    user_model = get_user_model()
    user = user_model.objects.create(
        username="dtypes-findings-admin",
        is_staff=True,
    )
    client.force_login(user)
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


def test_base_api_report_template_endpoints_shape() -> None:
    client = Client()

    by_name_res = client.get(
        "/base_api/report-templates/report_template_examples/colonoscopy_training_basic",
        secure=True,
    )
    assert by_name_res.status_code == 200, by_name_res.content.decode()
    by_name_payload = by_name_res.json()
    assert by_name_payload["name"] == "colonoscopy_training_basic"
    assert by_name_payload["examination"] == "colonoscopy"
    assert len(by_name_payload["report_sections"]) == 6
    assert by_name_payload["coverage_version"] == "report_concept_coverage_v1"

    by_exam_res = client.get(
        "/base_api/report-templates/by-examination/report_template_examples/colonoscopy",
        secure=True,
    )
    assert by_exam_res.status_code == 200, by_exam_res.content.decode()
    by_exam_payload = by_exam_res.json()
    assert isinstance(by_exam_payload, list)
    assert by_exam_payload
    assert by_exam_payload[0]["name"] == "colonoscopy_training_basic"

    core_concepts_res = client.get(
        "/base_api/core-concepts/report_template_examples",
        secure=True,
    )
    assert core_concepts_res.status_code == 200, core_concepts_res.content.decode()
    core_concepts_payload = core_concepts_res.json()
    assert "examination" in core_concepts_payload
    assert "finding" in core_concepts_payload
    assert core_concepts_payload["knowledge_base_module"] == "report_template_examples"
    assert core_concepts_payload["knowledge_base_version"] is not None


def test_base_api_report_template_runtime_validation() -> None:
    client = Client()

    missing_findings_res = client.post(
        "/base_api/report-templates/report_template_examples/colonoscopy_training_basic/validate",
        data=json.dumps(
            {
                "patient": "test_patient",
                "examination": "colonoscopy",
                "patient_findings": [],
            }
        ),
        content_type="application/json",
        secure=True,
    )
    assert missing_findings_res.status_code == 200, (
        missing_findings_res.content.decode()
    )
    missing_findings_payload = missing_findings_res.json()
    assert missing_findings_payload["template_name"] == "colonoscopy_training_basic"
    assert missing_findings_payload["ok"] is False
    assert any(
        issue["code"] == "finding_not_present"
        and issue["validator_name"] == "koloskopie_sedierung_dokumentiert"
        for issue in missing_findings_payload["issues"]
    )

    partial_findings_res = client.post(
        "/base_api/report-templates/report_template_examples/colonoscopy_training_basic/validate",
        data=json.dumps(
            {
                "patient": "test_patient",
                "examination": "colonoscopy",
                "patient_findings": [
                    {
                        "finding": "colonoscopy_deepest_viewed_location",
                        "patient_examination": "test_exam",
                        "patient_finding_classifications": [],
                        "patient_finding_interventions": [],
                    }
                ],
            }
        ),
        content_type="application/json",
        secure=True,
    )
    assert partial_findings_res.status_code == 200, (
        partial_findings_res.content.decode()
    )
    partial_findings_payload = partial_findings_res.json()
    assert partial_findings_payload["ok"] is False
    assert partial_findings_payload["evaluated_findings_count"] == 1
    assert partial_findings_payload["examination_validators"][0]["ok"] is False
    assert partial_findings_payload["findings_validators"][0]["ok"] is False


def test_base_api_report_template_runtime_validation_from_ledger() -> None:
    client = Client()
    examination = Examination.objects.create(name="colonoscopy")
    patient_examination = _create_patient_examination(examination)

    response = client.post(
        (
            "/base_api/report-templates/report_template_examples/"
            f"colonoscopy_training_basic/validate-from-ledger/{patient_examination.id}"
        ),
        secure=True,
    )

    assert response.status_code == 200, response.content.decode()
    payload = response.json()
    assert payload["template_name"] == "colonoscopy_training_basic"
    assert payload["evaluated_findings_count"] == 0
    assert payload["ok"] is False
    assert any(issue["code"] == "finding_not_present" for issue in payload["issues"])


def test_base_api_report_template_runtime_validation_from_ledger_not_found() -> None:
    client = Client()
    response = client.post(
        (
            "/base_api/report-templates/report_template_examples/"
            "colonoscopy_training_basic/validate-from-ledger/999999"
        ),
        secure=True,
    )
    assert response.status_code == 404
    assert "PatientExamination '999999' not found." in response.content.decode()


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


def test_base_api_patient_findings_validation_uses_examination_pinned_legacy_kb(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Client()
    user_model = get_user_model()
    user = user_model.objects.create(
        username="legacy-kb-user",
        is_staff=True,
    )
    client.force_login(user)
    examination, finding, classification, choice = _create_exam_graph()
    patient_examination = _create_patient_examination(examination)
    patient_examination.knowledge_base_module = "catalog_module"
    patient_examination.knowledge_base_version = "1.0.0"
    patient_examination.save(
        update_fields=["knowledge_base_module", "knowledge_base_version"]
    )

    monkeypatch.setattr(findings_routes, "_kb_lookup", _mock_kb_lookup)

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


def test_base_api_patient_findings_rejects_kb_choice_not_in_pinned_legacy_kb(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Client()
    user_model = get_user_model()
    user = user_model.objects.create(
        username="legacy-kb-user-2",
        is_staff=True,
    )
    client.force_login(user)
    examination, finding, _classification, _choice = _create_exam_graph()
    patient_examination = _create_patient_examination(examination)
    patient_examination.knowledge_base_module = "catalog_module"
    patient_examination.knowledge_base_version = "1.0.0"
    patient_examination.save(
        update_fields=["knowledge_base_module", "knowledge_base_version"]
    )

    forbidden_classification = FindingClassification.objects.create(
        name="forbidden_classification",
        description="Not in legacy KB",
    )
    forbidden_choice = FindingClassificationChoice.objects.create(
        name="forbidden_choice",
        description="Not in legacy KB",
        subcategories={},
        numerical_descriptors={},
    )
    forbidden_classification.choices.add(forbidden_choice)
    finding.finding_classifications.add(forbidden_classification)

    monkeypatch.setattr(findings_routes, "_kb_lookup", _mock_kb_lookup)

    create_res = client.post(
        "/base_api/patient-findings/",
        data=json.dumps(
            {
                "patient_examination": patient_examination.id,
                "finding": finding.id,
                "classifications": [
                    {
                        "classification": forbidden_classification.id,
                        "choice": forbidden_choice.id,
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
