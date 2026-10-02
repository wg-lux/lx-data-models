from django.test import Client


def test_reporting_languages_exposes_supported_lxdm_label_languages() -> None:
    response = Client().get("/base_api/reporting/languages", secure=True)

    assert response.status_code == 200
    assert response.json() == {
        "default_language": "de",
        "languages": [
            {"code": "de", "label": "Deutsch"},
            {"code": "en", "label": "English"},
        ],
    }
