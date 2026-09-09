from __future__ import annotations

import pytest

from lx_dtypes.models.contracts import (
    PatientFindingClassificationCreatePayload,
    ValidationError,
    dump_patient_finding_classification_create_payload,
    validate_patient_finding_classification_create_payload,
)


def test_patient_finding_classification_payload_accepts_canonical_names() -> None:
    payload = validate_patient_finding_classification_create_payload(
        {
            "patient_finding": 1,
            "classification": 2,
            "choice": 3,
        }
    )

    data = dump_patient_finding_classification_create_payload(payload)

    assert data == {
        "patient_finding_id": 1,
        "classification_id": 2,
        "classification_choice_id": 3,
    }


def test_patient_finding_classification_payload_accepts_legacy_id_names() -> None:
    payload = PatientFindingClassificationCreatePayload.model_validate(
        {
            "patient_finding_id": 4,
            "classification_id": 5,
            "classification_choice_id": 6,
        }
    )

    assert payload.patient_finding == 4
    assert payload.classification == 5
    assert payload.choice == 6


def test_patient_finding_classification_payload_rejects_invalid_ids() -> None:
    with pytest.raises(ValidationError):
        validate_patient_finding_classification_create_payload(
            {
                "patient_finding_id": 1,
                "classification_id": 0,
                "classification_choice_id": 2,
            }
        )


def test_patient_finding_classification_payload_rejects_string_ids() -> None:
    with pytest.raises(ValidationError):
        PatientFindingClassificationCreatePayload.model_validate(
            {
                "patient_finding_id": "4",
                "classification_id": 5,
                "classification_choice_id": 6,
            }
        )


def test_patient_finding_classification_payload_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        validate_patient_finding_classification_create_payload(
            {
                "patient_finding_id": 4,
                "classification_id": 5,
                "classification_choice_id": 6,
                "ignored": 7,
            }
        )
