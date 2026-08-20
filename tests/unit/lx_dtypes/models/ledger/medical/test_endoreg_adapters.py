from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone

import pytest

from lx_dtypes.models.ledger import ledger_models_lookup
from lx_dtypes.models.ledger.medical import (
    build_patient_medical_ledger,
    patient_disease_from_endoreg,
    patient_event_from_endoreg,
    patient_lab_sample_from_endoreg,
    patient_medication_schedule_from_endoreg,
)


@dataclass
class NamedRecord:
    pk: int
    name: str


@dataclass
class Relation:
    records: list[object] = field(default_factory=list)

    def all(self) -> list[object]:
        return self.records


@dataclass
class PatientDisease:
    pk: int
    patient: NamedRecord
    disease: NamedRecord
    classification_choices: Relation
    start_date: date | None = None
    end_date: date | None = None
    numerical_descriptors: dict[str, object] = field(default_factory=dict)
    subcategories: dict[str, object] = field(default_factory=dict)
    last_update: datetime | None = None


@dataclass
class PatientEvent:
    pk: int
    patient: NamedRecord
    event: NamedRecord
    date_start: date
    date_end: date | None = None
    description: str | None = None
    classification_choice: NamedRecord | None = None
    subcategories: dict[str, object] = field(default_factory=dict)
    numerical_descriptors: dict[str, object] = field(default_factory=dict)
    last_update: datetime | None = None


@dataclass
class PatientLabValue:
    pk: int
    patient: NamedRecord
    lab_value: NamedRecord
    sample: NamedRecord
    timestamp: datetime
    value: float | None = None
    value_str: str | None = None
    normal_range: dict[str, object] = field(default_factory=dict)
    unit: NamedRecord | None = None


@dataclass
class PatientLabSample:
    pk: int
    patient: NamedRecord
    sample_type: NamedRecord
    date: datetime
    values: Relation


@dataclass
class PatientMedication:
    pk: int
    patient: NamedRecord
    medication: NamedRecord
    intake_times: Relation
    medication_indication: NamedRecord | None = None
    unit: NamedRecord | None = None
    dosage: object | None = None
    active: bool = True


@dataclass
class PatientMedicationSchedule:
    pk: int
    patient: NamedRecord
    medication: Relation
    created_at: datetime
    updated_at: datetime


NOW = datetime(2026, 7, 29, 10, 30, tzinfo=timezone.utc)


def test_endoreg_patient_medical_graph_is_converted_without_orm_dependency() -> None:
    patient = NamedRecord(pk=7, name="patient-7")
    disease = PatientDisease(
        pk=11,
        patient=patient,
        disease=NamedRecord(pk=2, name="crohns_disease"),
        classification_choices=Relation([NamedRecord(pk=3, name="montreal_a2_l3_b1")]),
        start_date=date(2020, 1, 2),
        subcategories={"severity": "mild"},
        last_update=NOW,
    )
    event = PatientEvent(
        pk=12,
        patient=patient,
        event=NamedRecord(pk=4, name="first_diagnosis"),
        date_start=date(2020, 1, 2),
        classification_choice=NamedRecord(pk=5, name="confirmed"),
        last_update=NOW,
    )
    lab_value = PatientLabValue(
        pk=14,
        patient=patient,
        lab_value=NamedRecord(pk=6, name="crp"),
        sample=NamedRecord(pk=13, name="sample-13"),
        timestamp=NOW,
        value=4.2,
        normal_range={"min": 0.0, "max": 5.0},
        unit=NamedRecord(pk=7, name="mg/l"),
    )
    lab_sample = PatientLabSample(
        pk=13,
        patient=patient,
        sample_type=NamedRecord(pk=8, name="blood"),
        date=NOW,
        values=Relation([lab_value]),
    )
    medication = PatientMedication(
        pk=15,
        patient=patient,
        medication=NamedRecord(pk=9, name="mesalazine"),
        medication_indication=NamedRecord(pk=10, name="ibd"),
        intake_times=Relation([NamedRecord(pk=11, name="morning")]),
        unit=NamedRecord(pk=12, name="mg"),
        dosage={"morning": 500},
    )
    schedule = PatientMedicationSchedule(
        pk=16,
        patient=patient,
        medication=Relation([medication]),
        created_at=NOW,
        updated_at=NOW,
    )

    ledger = build_patient_medical_ledger(
        patient,
        diseases=[disease],
        events=[event],
        lab_samples=[lab_sample],
        lab_values=[lab_value],
        medications=[medication],
        medication_schedules=[schedule],
    )

    assert ledger.patient == "7"
    assert ledger.diseases[0].disease == "crohns_disease"
    assert ledger.events[0].classification_choice == "confirmed"
    assert ledger.lab_samples[0].values[0].normal_range.max == 5.0
    assert ledger.medications[0].dosage == {"morning": 500}
    assert ledger.medication_schedules[0].medications[0].medication == "mesalazine"
    assert ledger.medication_schedules[0].schedule_created_at == NOW
    assert ledger.external_ids == {"endoreg_db": "NamedRecord:7"}


def test_endoreg_primary_keys_produce_stable_ledger_identity() -> None:
    patient = NamedRecord(pk=7, name="patient-7")
    record = PatientDisease(
        pk=11,
        patient=patient,
        disease=NamedRecord(pk=2, name="crohns_disease"),
        classification_choices=Relation(),
    )

    first = patient_disease_from_endoreg(record)
    second = patient_disease_from_endoreg(record)

    assert first.uuid == second.uuid
    assert first.external_ids == {"endoreg_db": "PatientDisease:11"}


@pytest.mark.parametrize(
    ("adapter", "record", "field_name"),
    [
        (
            patient_disease_from_endoreg,
            PatientDisease(
                pk=1,
                patient=NamedRecord(pk=1, name="patient"),
                disease=None,  # type: ignore[arg-type]
                classification_choices=Relation(),
            ),
            "disease",
        ),
        (
            patient_event_from_endoreg,
            PatientEvent(
                pk=2,
                patient=NamedRecord(pk=1, name="patient"),
                event=NamedRecord(pk=2, name="event"),
                date_start=None,  # type: ignore[arg-type]
            ),
            "date_start",
        ),
    ],
)
def test_invalid_endoreg_records_fail_loudly(
    adapter: object, record: object, field_name: str
) -> None:
    with pytest.raises((TypeError, ValueError), match=field_name):
        adapter(record)  # type: ignore[operator]


def test_lab_sample_and_schedule_serialize_nested_records_as_ledger_links() -> None:
    patient = NamedRecord(pk=7, name="patient-7")
    lab_value = PatientLabValue(
        pk=14,
        patient=patient,
        lab_value=NamedRecord(pk=6, name="crp"),
        sample=NamedRecord(pk=13, name="sample-13"),
        timestamp=NOW,
    )
    sample = patient_lab_sample_from_endoreg(
        PatientLabSample(
            pk=13,
            patient=patient,
            sample_type=NamedRecord(pk=8, name="blood"),
            date=NOW,
            values=Relation([lab_value]),
        )
    )
    medication = PatientMedication(
        pk=15,
        patient=patient,
        medication=NamedRecord(pk=9, name="mesalazine"),
        intake_times=Relation(),
    )
    schedule = patient_medication_schedule_from_endoreg(
        PatientMedicationSchedule(
            pk=16,
            patient=patient,
            medication=Relation([medication]),
            created_at=NOW,
            updated_at=NOW,
        )
    )

    assert sample.serialized_model.values == str(sample.values[0].uuid)
    assert schedule.serialized_model.medications == str(schedule.medications[0].uuid)


def test_medical_models_are_available_from_the_ledger_registry() -> None:
    assert ledger_models_lookup["PatientDisease"].__name__ == "PatientDisease"
    assert ledger_models_lookup["PatientMedicalLedger"].__name__ == (
        "PatientMedicalLedger"
    )
