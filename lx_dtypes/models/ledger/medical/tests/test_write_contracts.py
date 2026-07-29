from __future__ import annotations

import pytest
from pydantic import ValidationError

from lx_dtypes.models.ledger.medical.Write import (
    PatientDiseaseCreate,
    PatientLabValueCreate,
    PatientMedicalLedgerCreate,
    PatientMedicationCreate,
    PatientMedicationScheduleCreate,
    PatientMedicationUpdate,
)


def test_medication_create_rejects_unknown_and_duplicate_intake_values() -> None:
    with pytest.raises(ValidationError):
        PatientMedicationCreate.model_validate(
            {
                "medication": "mesalazine",
                "intake_times": ["morning", "morning"],
                "unknown": True,
            }
        )


def test_medication_update_distinguishes_omitted_and_explicit_null_fields() -> None:
    clear_unit = PatientMedicationUpdate.model_validate({"unit": None})
    assert clear_unit.model_fields_set == {"unit"}

    with pytest.raises(ValidationError, match="active must not be null"):
        PatientMedicationUpdate.model_validate({"active": None})

    with pytest.raises(ValidationError, match="at least one"):
        PatientMedicationUpdate.model_validate({})


def test_schedule_create_requires_unique_positive_medication_ids() -> None:
    assert PatientMedicationScheduleCreate.model_validate(
        {"medication_ids": [1, 2]}
    ).medication_ids == [1, 2]

    with pytest.raises(ValidationError):
        PatientMedicationScheduleCreate.model_validate({"medication_ids": [1, 1]})
    with pytest.raises(ValidationError):
        PatientMedicationScheduleCreate.model_validate({"medication_ids": [0]})


def test_clinical_dates_values_and_unknown_fields_are_strict() -> None:
    with pytest.raises(ValidationError, match="end date"):
        PatientDiseaseCreate.model_validate(
            {
                "disease": "ulcer",
                "start_date": "2024-02-02",
                "end_date": "2024-02-01",
            }
        )

    with pytest.raises(ValidationError, match="exactly one"):
        PatientLabValueCreate.model_validate(
            {
                "lab_value": "crp",
                "value": 1.0,
                "value_str": "positive",
                "timestamp": "2024-03-01T09:00:00Z",
            }
        )

    with pytest.raises(ValidationError, match="timezone"):
        PatientLabValueCreate.model_validate(
            {
                "lab_value": "crp",
                "value": 1.0,
                "timestamp": "2024-03-01T09:00:00",
            }
        )


def test_aggregate_rejects_invalid_schedule_indices() -> None:
    with pytest.raises(ValidationError, match="out of range"):
        PatientMedicalLedgerCreate.model_validate(
            {
                "patient": "7",
                "medications": [{"medication": "mesalazine"}],
                "medication_schedules": [{"medication_indices": [1]}],
            }
        )
