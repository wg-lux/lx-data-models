from __future__ import annotations

import pytest

from lx_dtypes.models.contracts import CaseResolutionRequest, ValidationError


def test_case_resolution_create_requires_exactly_one_patient_target() -> None:
    with pytest.raises(ValidationError):
        CaseResolutionRequest.model_validate(
            {
                "action": "create",
                "examination_name": "colonoscopy",
            }
        )

    with pytest.raises(ValidationError):
        CaseResolutionRequest.model_validate(
            {
                "action": "create",
                "patient_id": 1,
                "new_patient": {"first_name": "Max", "last_name": "Mustermann"},
                "examination_name": "colonoscopy",
            }
        )


def test_case_resolution_defer_disallows_linkage_fields() -> None:
    with pytest.raises(ValidationError):
        CaseResolutionRequest.model_validate(
            {
                "action": "defer",
                "patient_id": 1,
            }
        )


def test_case_resolution_attach_requires_patient_examination() -> None:
    with pytest.raises(ValidationError):
        CaseResolutionRequest.model_validate({"action": "attach"})
