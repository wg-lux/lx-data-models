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


def test_medication_create_rejects_unknown_fields_and_invalid_dosing() -> None:
    with pytest.raises(ValidationError):
        PatientMedicationCreate.model_validate(
            {
                "medication": "mesalazine",
                "unknown": True,
            }
        )

    with pytest.raises(ValidationError):
        PatientMedicationCreate.model_validate(
            {
                "medication": "mesalazine",
                "dosing": {"morning": "0"},
            }
        )

    with pytest.raises(ValidationError):
        PatientMedicationCreate.model_validate(
            {
                "medication": "mesalazine",
                "dosing": {"morning": "1", "free_text": "once daily"},
            }
        )


def test_medication_create_rejects_entirely_blank_entry() -> None:
    with pytest.raises(ValidationError, match="at least one identifying"):
        PatientMedicationCreate.model_validate({})


def test_medication_update_distinguishes_omitted_and_explicit_null_fields() -> None:
    clear_unit = PatientMedicationUpdate.model_validate({"unit": None})
    assert clear_unit.model_fields_set == {"unit"}

    with pytest.raises(ValidationError, match="active must not be null"):
        PatientMedicationUpdate.model_validate({"active": None})

    with pytest.raises(ValidationError, match="at least one"):
        PatientMedicationUpdate.model_validate({})


def test_schedule_create_requires_unique_positive_medication_ids() -> None:
    schedule = PatientMedicationScheduleCreate.model_validate(
        {
            "blocks": [
                {
                    "rows": [
                        {"kind": "medication", "medication_id": 1},
                        {"kind": "medication", "medication_id": 2},
                    ]
                }
            ]
        }
    )
    assert [row.medication_id for row in schedule.blocks[0].rows] == [1, 2]

    with pytest.raises(ValidationError):
        PatientMedicationScheduleCreate.model_validate(
            {
                "blocks": [
                    {
                        "rows": [
                            {"kind": "medication", "medication_id": 1},
                            {"kind": "medication", "medication_id": 1},
                        ]
                    }
                ]
            }
        )
    with pytest.raises(ValidationError):
        PatientMedicationScheduleCreate.model_validate(
            {"blocks": [{"rows": [{"kind": "medication", "medication_id": 0}]}]}
        )


def test_schedule_create_requires_heading_from_second_block() -> None:
    with pytest.raises(ValidationError, match="heading"):
        PatientMedicationScheduleCreate.model_validate(
            {
                "blocks": [
                    {"rows": [{"kind": "medication", "medication_id": 1}]},
                    {"rows": [{"kind": "medication", "medication_id": 2}]},
                ]
            }
        )

    schedule = PatientMedicationScheduleCreate.model_validate(
        {
            "blocks": [
                {"rows": [{"kind": "medication", "medication_id": 1}]},
                {
                    "heading": {"code": 411},
                    "rows": [{"kind": "medication", "medication_id": 2}],
                },
            ]
        }
    )
    assert schedule.blocks[1].heading is not None
    assert schedule.blocks[1].heading.code == 411


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
                "medication_schedules": [
                    {
                        "blocks": [
                            {"rows": [{"kind": "medication", "medication_index": 1}]}
                        ]
                    }
                ],
            }
        )


def test_aggregate_rejects_duplicate_schedule_indices() -> None:
    with pytest.raises(ValidationError, match="unique"):
        PatientMedicalLedgerCreate.model_validate(
            {
                "patient": "7",
                "medications": [{"medication": "mesalazine"}],
                "medication_schedules": [
                    {
                        "blocks": [
                            {
                                "rows": [
                                    {"kind": "medication", "medication_index": 0},
                                    {"kind": "medication", "medication_index": 0},
                                ]
                            }
                        ]
                    }
                ],
            }
        )


@pytest.mark.parametrize(
    "period",
    [
        {"end_at": "2026-01-02T10:00:00Z"},
        {"start_at": "2026-01-02T10:00:00Z", "end_at": "2026-01-01T10:00:00Z"},
        {"start_at": "2026-01-01T10:00:00"},
        {"start_at": 123},
    ],
)
def test_medication_rejects_invalid_periods(period: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        PatientMedicationCreate.model_validate({"medication": "example", **period})


def test_medication_period_roundtrip_and_open_end() -> None:
    from lx_dtypes.models.ledger.medical import PatientMedication

    payload = PatientMedicationCreate.model_validate(
        {
            "medication": "example",
            "start_at": "2026-01-01T10:00:00+02:00",
            "end_at": "2026-01-01T09:00:00Z",
        }
    )
    record = PatientMedication.model_validate({"patient": "1", **payload.model_dump()})
    assert record.start_at == payload.start_at
    assert (
        PatientMedication.model_validate_json(record.model_dump_json()).end_at
        == payload.end_at
    )
    assert record.ddict.get("start_at") == payload.start_at
    assert PatientMedicationCreate(medication="example").start_at is None


@pytest.mark.parametrize(
    "bounds",
    [
        {"min": 5.0, "max": 1.0},
        {"min": float("nan")},
        {"max": float("inf")},
        {"female": {"min": 5.0, "max": 1.0}},
    ],
)
def test_measurement_rejects_invalid_normal_range(bounds: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        PatientLabValueCreate.model_validate(
            {
                "lab_value": "example",
                "value": 0.0,
                "timestamp": "2026-01-01T10:00:00Z",
                "normal_range": bounds,
            }
        )


@pytest.mark.parametrize("case_id", [0, -1, True, "1"])
def test_aggregate_rejects_invalid_case_ids(case_id: object) -> None:
    with pytest.raises(ValidationError):
        PatientMedicalLedgerCreate.model_validate({"patient": "1", "case_id": case_id})
