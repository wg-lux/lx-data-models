import json
from pathlib import Path
from typing import Any

from django.test import Client
import pytest

from lx_dtypes.django.api import main as api_main
from lx_dtypes.models.interface.KnowledgeBaseResolver import (
    KnowledgeBaseVersionNotFoundError,
)


def test_report_template_api_by_name() -> None:
    client = Client()
    response = client.get(
        "/base_api/report-templates/report_template_examples/star_upper_gi_main",
        secure=True,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "star_upper_gi_main"
    assert payload["examination"] == "star_upper_gi_endoscopy"


def test_report_template_api_by_examination() -> None:
    client = Client()
    response = client.get(
        "/base_api/report-templates/by-examination/report_template_examples/star_upper_gi_endoscopy",
        secure=True,
    )
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert any(t["name"] == "star_upper_gi_main" for t in payload)


def test_report_template_runtime_validation_api() -> None:
    client = Client()
    response = client.post(
        "/base_api/report-templates/report_template_examples/star_upper_gi_main/validate",
        data=json.dumps(
            {
                "patient": "test_patient",
                "examination": "star_upper_gi_endoscopy",
                "patient_findings": [
                    {
                        "finding": "star_upper_gi_mucosa_esophagus_abnormal",
                        "patient_examination": "test_exam",
                        "patient_finding_classifications": [],
                        "patient_finding_interventions": [],
                    },
                    {
                        "finding": "esophagus_polyp",
                        "patient_examination": "test_exam",
                        "patient_finding_classifications": [
                            {
                                "patient_finding": "test_finding",
                                "patient_finding_classification_choices": [
                                    {
                                        "classification": "size_mm",
                                        "classification_choice": "size_mm",
                                        "patient_finding_classifications": "test_classifications",
                                        "patient_finding_classification_choice_descriptors": [
                                            {
                                                "descriptor_value": 12,
                                                "classification_choice_descriptor": "length_mm_descriptor",
                                                "patient_finding_classification_choice": "test_choice",
                                            }
                                        ],
                                    }
                                ],
                            }
                        ],
                        "patient_finding_interventions": [],
                    },
                ],
            }
        ),
        content_type="application/json",
        secure=True,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["template_name"] == "star_upper_gi_main"
    assert payload["ok"] is False
    assert any(
        issue["code"] == "missing_required_classification"
        for issue in payload["issues"]
    )


def test_report_template_runtime_validation_api_uses_payload_kb_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Client()
    captured: dict[str, str | None] = {}
    fallback_kb = api_main._kb_loader().load_knowledge_base("report_template_examples")

    def _fake_load_knowledge_base(
        module_name: str,
        *,
        version: str | None = None,
        input_dirs: list[Path] | None = None,
    ) -> Any:
        del input_dirs
        captured["module_name"] = module_name
        captured["version"] = version
        return fallback_kb

    monkeypatch.setattr(api_main, "load_knowledge_base", _fake_load_knowledge_base)

    response = client.post(
        "/base_api/report-templates/report_template_examples/star_upper_gi_main/validate",
        data=json.dumps(
            {
                "patient": "test_patient",
                "examination": "star_upper_gi_endoscopy",
                "knowledge_base_module": "report_template_examples",
                "knowledge_base_version": "0.1.0",
                "patient_findings": [
                    {
                        "finding": "star_upper_gi_mucosa_esophagus_abnormal",
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

    assert response.status_code == 200
    assert captured == {
        "module_name": "report_template_examples",
        "version": "0.1.0",
    }


def test_report_template_definition_validation_api() -> None:
    client = Client()
    response = client.get(
        "/base_api/report-templates/report_template_examples/star_upper_gi_main/validate-definition",
        secure=True,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["lifecycle_status"] == "published"
    assert payload["can_preview"] is True
    assert payload["can_publish"] is True


def test_single_validator_runtime_validation_api() -> None:
    client = Client()
    response = client.post(
        "/base_api/validators/report_template_examples/findings_validator/polyp_has_lst_if_large/validate",
        data=json.dumps(
            {
                "patient": "test_patient",
                "examination": "star_upper_gi_endoscopy",
                "patient_findings": [
                    {
                        "finding": "esophagus_polyp",
                        "patient_examination": "test_exam",
                        "patient_finding_classifications": [
                            {
                                "patient_finding": "test_finding",
                                "patient_finding_classification_choices": [
                                    {
                                        "classification": "size_mm",
                                        "classification_choice": "size_mm",
                                        "patient_finding_classifications": "test_classifications",
                                        "patient_finding_classification_choice_descriptors": [
                                            {
                                                "descriptor_value": 12,
                                                "classification_choice_descriptor": "length_mm_descriptor",
                                                "patient_finding_classification_choice": "test_choice",
                                            }
                                        ],
                                    }
                                ],
                            }
                        ],
                        "patient_finding_interventions": [],
                    }
                ],
            }
        ),
        content_type="application/json",
        secure=True,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "polyp_has_lst_if_large"
    assert payload["ok"] is False


def test_report_template_runtime_validation_api_rejects_semantically_forbidden_payload() -> (
    None
):
    client = Client()
    response = client.post(
        "/base_api/report-templates/report_template_examples/star_upper_gi_main/validate",
        data=json.dumps(
            {
                "patient": "test_patient",
                "examination": "colonoscopy",
                "patient_findings": [
                    {
                        "finding": "esophagus_polyp",
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
    assert response.status_code == 422
    assert "does not match report template" in response.content.decode()


def test_report_template_runtime_validation_api_rejects_payload_module_conflict() -> (
    None
):
    client = Client()
    response = client.post(
        "/base_api/report-templates/report_template_examples/star_upper_gi_main/validate",
        data=json.dumps(
            {
                "patient": "test_patient",
                "examination": "star_upper_gi_endoscopy",
                "knowledge_base_module": "other_module",
                "knowledge_base_version": "0.1.0",
                "patient_findings": [],
            }
        ),
        content_type="application/json",
        secure=True,
    )
    assert response.status_code == 409
    assert "does not match route module" in response.content.decode()


def test_report_template_runtime_validation_api_rejects_unavailable_payload_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Client()

    def _missing_version(*args: Any, **kwargs: Any) -> Any:
        raise KnowledgeBaseVersionNotFoundError("missing")

    monkeypatch.setattr(api_main, "load_knowledge_base", _missing_version)

    response = client.post(
        "/base_api/report-templates/report_template_examples/star_upper_gi_main/validate",
        data=json.dumps(
            {
                "patient": "test_patient",
                "examination": "star_upper_gi_endoscopy",
                "knowledge_base_version": "9.9.9",
                "patient_findings": [],
            }
        ),
        content_type="application/json",
        secure=True,
    )
    assert response.status_code == 409
    assert "not provisioned locally" in response.content.decode()


def test_core_concepts_api() -> None:
    client = Client()
    response = client.get(
        "/base_api/core-concepts/report_template_examples",
        secure=True,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["module_name"] == "report_template_examples"
    assert isinstance(payload["finding"], list)
    assert isinstance(payload["classification"], list)
