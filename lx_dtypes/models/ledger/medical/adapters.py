from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime
from typing import Protocol, cast
from uuid import UUID, uuid5

from lx_dtypes.models.contracts.json_types import JsonObject, JsonValue
from lx_dtypes.models.contracts.lab_value import LabValueNormalRangeData

from .Pydantic import (
    PatientDisease,
    PatientEvent,
    PatientLabSample,
    PatientLabValue,
    PatientMedicalLedger,
    PatientMedication,
    PatientMedicationSchedule,
)

ENDOREG_DB_LEDGER_NAMESPACE = UUID("57006ca0-0840-5a4a-8569-d33f60ba4549")


class DjangoRelationLike(Protocol):
    def all(self) -> Iterable[object]: ...


def _required_reference(value: object, field_name: str) -> str:
    reference = _optional_reference(value)
    if reference is None:
        raise ValueError(f"EndoReg medical record is missing '{field_name}'.")
    return reference


def _required_identity_reference(value: object, field_name: str) -> str:
    reference = _optional_identity_reference(value)
    if reference is None:
        raise ValueError(f"EndoReg medical record is missing '{field_name}'.")
    return reference


def _optional_identity_reference(value: object | None) -> str | None:
    if value is None:
        return None
    primary_key = getattr(value, "pk", None)
    if primary_key is None:
        primary_key = getattr(value, "id", None)
    if primary_key is None:
        return None
    return str(primary_key)


def _optional_reference(value: object | None) -> str | None:
    if value is None:
        return None
    name = str(getattr(value, "name", "") or "").strip()
    if name:
        return name
    primary_key = getattr(value, "pk", None)
    if primary_key is None:
        primary_key = getattr(value, "id", None)
    if primary_key is None:
        return None
    return str(primary_key)


def _relation_values(value: object | None) -> list[object]:
    if value is None:
        return []
    all_method = getattr(value, "all", None)
    if callable(all_method):
        return list(cast(DjangoRelationLike, value).all())
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes, dict)):
        return list(value)
    raise TypeError("Expected a Django relation manager or an iterable.")


def _json_object(value: object | None, field_name: str) -> JsonObject:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise TypeError(f"EndoReg field '{field_name}' must be a JSON object.")
    return cast(JsonObject, value)


def _json_value(value: object | None, field_name: str) -> JsonValue:
    if value is None or isinstance(value, (str, int, float, bool, list, dict)):
        return cast(JsonValue, value)
    raise TypeError(f"EndoReg field '{field_name}' is not JSON-compatible.")


def _required_datetime(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"EndoReg field '{field_name}' must be a datetime.")
    return value


def _required_bool(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"EndoReg field '{field_name}' must be a boolean.")
    return value


def _optional_datetime(value: object | None, field_name: str) -> datetime | None:
    if value is None:
        return None
    return _required_datetime(value, field_name)


def _required_date(value: object, field_name: str) -> date:
    if not isinstance(value, date) or isinstance(value, datetime):
        raise TypeError(f"EndoReg field '{field_name}' must be a date.")
    return value


def _optional_date(value: object | None, field_name: str) -> date | None:
    if value is None:
        return None
    return _required_date(value, field_name)


def _ledger_identity(record: object) -> dict[str, object]:
    primary_key = getattr(record, "pk", None)
    if primary_key is None:
        primary_key = getattr(record, "id", None)
    if primary_key is None:
        raise ValueError("EndoReg medical record is missing a primary key.")
    model_name = type(record).__name__
    external_id = f"{model_name}:{primary_key}"
    return {
        "uuid": str(uuid5(ENDOREG_DB_LEDGER_NAMESPACE, external_id)),
        "external_ids": {"endoreg_db": external_id},
    }


def patient_disease_from_endoreg(record: object) -> PatientDisease:
    return PatientDisease.model_validate(
        {
            **_ledger_identity(record),
            "patient": _required_identity_reference(
                getattr(record, "patient", None), "patient"
            ),
            "disease": _required_reference(getattr(record, "disease", None), "disease"),
            "classification_choices": [
                _required_reference(item, "classification_choices")
                for item in _relation_values(
                    getattr(record, "classification_choices", None)
                )
            ],
            "start_date": _optional_date(
                getattr(record, "start_date", None), "start_date"
            ),
            "end_date": _optional_date(getattr(record, "end_date", None), "end_date"),
            "numerical_descriptors": _json_object(
                getattr(record, "numerical_descriptors", None),
                "numerical_descriptors",
            ),
            "subcategories": _json_object(
                getattr(record, "subcategories", None), "subcategories"
            ),
            "last_update": _optional_datetime(
                getattr(record, "last_update", None), "last_update"
            ),
        }
    )


def patient_event_from_endoreg(record: object) -> PatientEvent:
    return PatientEvent.model_validate(
        {
            **_ledger_identity(record),
            "patient": _required_identity_reference(
                getattr(record, "patient", None), "patient"
            ),
            "event": _required_reference(getattr(record, "event", None), "event"),
            "date_start": _required_date(
                getattr(record, "date_start", None), "date_start"
            ),
            "date_end": _optional_date(getattr(record, "date_end", None), "date_end"),
            "description": getattr(record, "description", None),
            "classification_choice": _optional_reference(
                getattr(record, "classification_choice", None)
            ),
            "subcategories": _json_object(
                getattr(record, "subcategories", None), "subcategories"
            ),
            "numerical_descriptors": _json_object(
                getattr(record, "numerical_descriptors", None),
                "numerical_descriptors",
            ),
            "last_update": _optional_datetime(
                getattr(record, "last_update", None), "last_update"
            ),
        }
    )


def patient_lab_value_from_endoreg(record: object) -> PatientLabValue:
    normal_range = LabValueNormalRangeData.model_validate(
        _json_object(getattr(record, "normal_range", None), "normal_range")
    )
    return PatientLabValue.model_validate(
        {
            **_ledger_identity(record),
            "patient": _optional_identity_reference(getattr(record, "patient", None)),
            "lab_value": _required_reference(
                getattr(record, "lab_value", None), "lab_value"
            ),
            "value": getattr(record, "value", None),
            "value_str": getattr(record, "value_str", None),
            "sample": _optional_identity_reference(getattr(record, "sample", None)),
            "timestamp": _required_datetime(
                getattr(record, "timestamp", None), "timestamp"
            ),
            "normal_range": normal_range,
            "unit": _optional_reference(getattr(record, "unit", None)),
        }
    )


def patient_lab_sample_from_endoreg(record: object) -> PatientLabSample:
    return PatientLabSample.model_validate(
        {
            **_ledger_identity(record),
            "patient": _required_identity_reference(
                getattr(record, "patient", None), "patient"
            ),
            "sample_type": _required_reference(
                getattr(record, "sample_type", None), "sample_type"
            ),
            "date": _required_datetime(getattr(record, "date", None), "date"),
            "values": [
                patient_lab_value_from_endoreg(item)
                for item in _relation_values(getattr(record, "values", None))
            ],
        }
    )


def patient_medication_from_endoreg(record: object) -> PatientMedication:
    return PatientMedication.model_validate(
        {
            **_ledger_identity(record),
            "patient": _required_identity_reference(
                getattr(record, "patient", None), "patient"
            ),
            "medication_indication": _optional_reference(
                getattr(record, "medication_indication", None)
            ),
            "medication": _required_reference(
                getattr(record, "medication", None), "medication"
            ),
            "intake_times": [
                _required_reference(item, "intake_times")
                for item in _relation_values(getattr(record, "intake_times", None))
            ],
            "unit": _optional_reference(getattr(record, "unit", None)),
            "dosage": _json_value(getattr(record, "dosage", None), "dosage"),
            "active": _required_bool(getattr(record, "active", True), "active"),
        }
    )


def patient_medication_schedule_from_endoreg(
    record: object,
) -> PatientMedicationSchedule:
    return PatientMedicationSchedule.model_validate(
        {
            **_ledger_identity(record),
            "patient": _required_identity_reference(
                getattr(record, "patient", None), "patient"
            ),
            "medications": [
                patient_medication_from_endoreg(item)
                for item in _relation_values(getattr(record, "medication", None))
            ],
            "schedule_created_at": _required_datetime(
                getattr(record, "created_at", None), "created_at"
            ),
            "updated_at": _required_datetime(
                getattr(record, "updated_at", None), "updated_at"
            ),
        }
    )


def build_patient_medical_ledger(
    patient: object,
    *,
    diseases: Iterable[object] = (),
    events: Iterable[object] = (),
    lab_samples: Iterable[object] = (),
    lab_values: Iterable[object] = (),
    medications: Iterable[object] = (),
    medication_schedules: Iterable[object] = (),
) -> PatientMedicalLedger:
    patient_reference = _required_identity_reference(patient, "patient")
    patient_identity = _ledger_identity(patient)
    return PatientMedicalLedger.model_validate(
        {
            **patient_identity,
            "patient": patient_reference,
            "diseases": [patient_disease_from_endoreg(item) for item in diseases],
            "events": [patient_event_from_endoreg(item) for item in events],
            "lab_samples": [
                patient_lab_sample_from_endoreg(item) for item in lab_samples
            ],
            "lab_values": [patient_lab_value_from_endoreg(item) for item in lab_values],
            "medications": [
                patient_medication_from_endoreg(item) for item in medications
            ],
            "medication_schedules": [
                patient_medication_schedule_from_endoreg(item)
                for item in medication_schedules
            ],
        }
    )


__all__ = [
    "ENDOREG_DB_LEDGER_NAMESPACE",
    "build_patient_medical_ledger",
    "patient_disease_from_endoreg",
    "patient_event_from_endoreg",
    "patient_lab_sample_from_endoreg",
    "patient_lab_value_from_endoreg",
    "patient_medication_from_endoreg",
    "patient_medication_schedule_from_endoreg",
]
