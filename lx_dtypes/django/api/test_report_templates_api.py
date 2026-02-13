import pytest
from django.test import Client


@pytest.mark.django_db
def test_report_template_api_by_name() -> None:
    client = Client()
    response = client.get(
        "/base_api/report-templates/report_template_examples/star_upper_gi_main"
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "star_upper_gi_main"
    assert payload["examination"] == "star_upper_gi_endoscopy"


@pytest.mark.django_db
def test_report_template_api_by_examination() -> None:
    client = Client()
    response = client.get(
        "/base_api/report-templates/by-examination/report_template_examples/star_upper_gi_endoscopy"
    )
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert any(t["name"] == "star_upper_gi_main" for t in payload)
