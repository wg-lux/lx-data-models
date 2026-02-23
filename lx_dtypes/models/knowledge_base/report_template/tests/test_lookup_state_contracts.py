from __future__ import annotations

import pytest
from pydantic import ValidationError

from lx_dtypes.models.knowledge_base.report_template.LookupState import (
    LookupInitRequest,
    LookupPartsPatchRequest,
    LookupState,
    build_lookup_recompute_response,
    normalize_lookup_keys,
    validate_lookup_parts_response,
    validate_lookup_state,
    validate_lookup_updates,
)


def test_normalize_lookup_keys_maps_legacy_camelcase() -> None:
    payload = {
        "selectedRequirementSetIds": [1, 2],
        "selectedChoices": {"10": {"choice_id": 3}},
    }
    normalized = normalize_lookup_keys(payload)
    assert normalized["selected_requirement_set_ids"] == [1, 2]
    assert normalized["selected_choices"] == {"10": {"choice_id": 3}}


def test_normalize_lookup_keys_prefers_canonical_when_both_present() -> None:
    payload = {
        "selectedRequirementSetIds": [1],
        "selected_requirement_set_ids": [2],
    }
    normalized = normalize_lookup_keys(payload)
    assert normalized["selected_requirement_set_ids"] == [2]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("12", 12),
        (["12"], 12),
        ((12,), 12),
    ],
)
def test_lookup_init_request_coerces_patient_examination_id(raw: object, expected: int) -> None:
    req = LookupInitRequest.model_validate({"patient_examination_id": raw})
    assert req.patient_examination_id == expected


def test_lookup_init_request_normalizes_user_tags() -> None:
    req = LookupInitRequest.model_validate(
        {"patient_examination_id": 1, "user_tags": ("a", "", None, "b")}
    )
    assert req.user_tags == ["a", "b"]


def test_lookup_init_request_rejects_invalid_patient_examination_id() -> None:
    with pytest.raises(ValidationError):
        LookupInitRequest.model_validate({"patient_examination_id": 0})


def test_lookup_parts_patch_request_normalizes_legacy_keys_in_updates() -> None:
    req = LookupPartsPatchRequest.model_validate(
        {"updates": {"selectedRequirementSetIds": ["1"], "selectedChoices": {}}}
    )
    assert req.updates["selected_requirement_set_ids"] == ["1"]
    assert req.updates["selected_choices"] == {}


def test_lookup_parts_patch_request_rejects_empty_updates() -> None:
    with pytest.raises(ValidationError):
        LookupPartsPatchRequest.model_validate({"updates": {}})


def test_lookup_state_normalizes_legacy_keys_and_selected_ids() -> None:
    state = LookupState.model_validate(
        {
            "patient_examination_id": 1,
            "selectedRequirementSetIds": ["2", 3],
            "selectedChoices": {"10": {"choice_id": 1}},
        }
    )
    assert state.selected_requirement_set_ids == [2, 3]
    assert state.selected_choices == {"10": {"choice_id": 1}}


def test_validate_lookup_state_returns_ddict_like_payload() -> None:
    payload = validate_lookup_state({"patient_examination_id": 42})
    assert payload is not None
    assert payload["patient_examination_id"] == 42
    assert payload["candidate_requirement_set_ids"] == []
    assert payload["candidate_requirement_set_confidence"] == 0.0


def test_validate_lookup_parts_response_returns_only_requested_keys() -> None:
    payload = {
        "patient_examination_id": 1,
        "selectedRequirementSetIds": [5],
        "selectedChoices": {"10": {"choice_id": 2}},
    }
    out = validate_lookup_parts_response(
        payload,
        requested_keys=["selectedRequirementSetIds", "patient_examination_id"],
    )
    assert out == {
        "selected_requirement_set_ids": [5],
        "patient_examination_id": 1,
    }


def test_validate_lookup_updates_rejects_unknown_keys() -> None:
    with pytest.raises(ValidationError):
        validate_lookup_updates({"unknown_key": True})


def test_build_lookup_recompute_response_wraps_updates_strictly() -> None:
    response = build_lookup_recompute_response(
        "tok123",
        {
            "requirement_status": {"1": True},
            "candidate_requirement_set_ids": [11, 12],
            "candidate_requirement_set_confidence": 0.8,
        },
    )
    assert response["ok"] is True
    assert response["token"] == "tok123"
    assert response["updates"]["requirement_status"] == {"1": True}
