import json

from django.test import Client


def _requirement_set_id(payload: list[dict], name: str) -> int:
    for row in payload:
        if row.get("name") == name:
            return int(row["id"])
    raise AssertionError(f"Requirement set '{name}' not found in payload")


def test_requirement_sets_list_api() -> None:
    client = Client()
    response = client.get("/base_api/requirement-sets", secure=True)
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert any(row.get("name") == "star_upper_gi_main" for row in payload)
    first = payload[0]
    assert isinstance(first.get("requirements"), list)
    assert "id" in first
    assert "type" in first


def test_requirement_set_detail_api() -> None:
    client = Client()
    list_response = client.get("/base_api/requirement-sets", secure=True)
    assert list_response.status_code == 200
    set_id = _requirement_set_id(list_response.json(), "star_upper_gi_main")

    detail_response = client.get(f"/base_api/requirement-sets/{set_id}", secure=True)
    assert detail_response.status_code == 200
    payload = detail_response.json()
    assert payload["id"] == set_id
    assert payload["name"] == "star_upper_gi_main"
    assert isinstance(payload["requirements"], list)


def test_evaluate_requirement_set_api_with_dtypes_validators() -> None:
    client = Client()
    list_response = client.get("/base_api/requirement-sets", secure=True)
    assert list_response.status_code == 200
    set_id = _requirement_set_id(list_response.json(), "star_upper_gi_main")

    response = client.post(
        "/base_api/evaluate-requirement-set",
        data=json.dumps(
            {
                "requirement_set_ids": [set_id],
                "reported_findings": [
                    {
                        "finding": "star_upper_gi_mucosa_esophagus_abnormal",
                        "classifications": [],
                    },
                    {
                        "finding": "esophagus_polyp",
                        "classifications": [{"classification": "size_mm", "value": 12}],
                    },
                ],
            }
        ),
        content_type="application/json",
        secure=True,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["sets_evaluated"] == 1
    assert any(
        row["requirement_name"] == "polyp_has_lst_if_large" and row["met"] is False
        for row in payload["results"]
    )
