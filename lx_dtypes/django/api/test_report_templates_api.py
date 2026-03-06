import json
from django.test import Client


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
                "findings": [
                    {
                        "finding": "star_upper_gi_mucosa_esophagus_abnormal",
                        "classifications": [],
                    },
                    {
                        "finding": "esophagus_polyp",
                        "classifications": [{"classification": "size_mm", "value": 12}],
                    },
                ]
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
