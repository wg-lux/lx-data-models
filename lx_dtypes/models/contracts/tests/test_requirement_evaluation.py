from __future__ import annotations

import pytest

from lx_dtypes.models.contracts import (
    RequirementEvaluationRequest,
    RequirementEvaluationResponse,
    ValidationError,
)


def test_requirement_evaluation_request_coerces_payload() -> None:
    payload = RequirementEvaluationRequest.model_validate(
        {
            "patient_examination_id": "5",
            "requirement_set_ids": ["1", 2],
        }
    )

    assert payload.patient_examination_id == 5
    assert payload.requirement_set_ids == [1, 2]


def test_requirement_evaluation_request_rejects_invalid_requirement_set_ids() -> None:
    with pytest.raises(ValidationError):
        RequirementEvaluationRequest.model_validate(
            {
                "patient_examination_id": 1,
                "requirement_set_ids": "invalid",
            }
        )


def test_requirement_evaluation_response_round_trips() -> None:
    payload = RequirementEvaluationResponse.model_validate(
        {
            "ok": True,
            "errors": [],
            "meta": {
                "patient_examination_id": 7,
                "sets_evaluated": 1,
                "requirements_evaluated": 2,
                "status": "ok",
            },
            "results": [
                {
                    "requirement_set_id": 1,
                    "requirement_set_name": "1",
                    "requirement_name": "some requirement",
                    "met": True,
                    "details": "Voraussetzung erfüllt",
                    "error": None,
                    "status": "PASSED",
                }
            ],
        }
    )

    assert payload.ok is True
    assert payload.meta.patient_examination_id == 7
    assert payload.results[0].status == "PASSED"
