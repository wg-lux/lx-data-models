"""Strict write contracts for patient-owned medical persistence."""

from __future__ import annotations

from datetime import date, datetime
from math import isfinite
from typing import Self

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from lx_dtypes.models.contracts.json_types import JsonObject, JsonValue
from lx_dtypes.models.contracts.lab_value import LabValueNormalRangeData


class _MedicalWriteModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        str_strip_whitespace=True,
    )


def _validate_references(values: list[str]) -> list[str]:
    if any(not value for value in values):
        raise ValueError("references must not contain empty values")
    if len(values) != len(set(values)):
        raise ValueError("references must be unique")
    return values


def _validate_ids(values: list[int]) -> list[int]:
    if any(value <= 0 for value in values):
        raise ValueError("record ids must be positive")
    if len(values) != len(set(values)):
        raise ValueError("record ids must be unique")
    return values


def _validate_date_range(start: date, end: date | None) -> None:
    if end is not None and end < start:
        raise ValueError("end date must not be earlier than start date")


def _parse_date(value: object) -> object:
    if isinstance(value, str):
        return date.fromisoformat(value)
    return value


def _parse_aware_datetime(value: object) -> object:
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("datetime must include a timezone offset")
        return parsed
    return value


class PatientDiseaseCreate(_MedicalWriteModel):
    disease: str = Field(min_length=1)
    classification_choices: list[str] = Field(default_factory=list)
    start_date: date | None = None
    end_date: date | None = None
    numerical_descriptors: JsonObject = Field(default_factory=dict)
    subcategories: JsonObject = Field(default_factory=dict)

    @field_validator("classification_choices")
    @classmethod
    def validate_choices(cls, values: list[str]) -> list[str]:
        return _validate_references(values)

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def parse_dates(cls, value: object) -> object:
        return _parse_date(value)

    @model_validator(mode="after")
    def validate_dates(self) -> Self:
        if self.start_date is None and self.end_date is not None:
            raise ValueError("end_date requires start_date")
        if self.start_date is not None:
            _validate_date_range(self.start_date, self.end_date)
        return self


class PatientEventCreate(_MedicalWriteModel):
    event: str = Field(min_length=1)
    date_start: date
    date_end: date | None = None
    description: str | None = None
    classification_choice: str | None = Field(default=None, min_length=1)
    subcategories: JsonObject = Field(default_factory=dict)
    numerical_descriptors: JsonObject = Field(default_factory=dict)

    @field_validator("date_start", "date_end", mode="before")
    @classmethod
    def parse_dates(cls, value: object) -> object:
        return _parse_date(value)

    @model_validator(mode="after")
    def validate_dates(self) -> Self:
        _validate_date_range(self.date_start, self.date_end)
        return self


class PatientLabValueCreate(_MedicalWriteModel):
    lab_value: str = Field(min_length=1)
    value: float | None = None
    value_str: str | None = Field(default=None, min_length=1)
    timestamp: AwareDatetime
    normal_range: LabValueNormalRangeData = Field(
        default_factory=LabValueNormalRangeData
    )
    unit: str | None = Field(default=None, min_length=1)

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_timestamp(cls, value: object) -> object:
        return _parse_aware_datetime(value)

    @model_validator(mode="after")
    def validate_value_shape(self) -> Self:
        if (self.value is None) == (self.value_str is None):
            raise ValueError("exactly one of value and value_str must be provided")
        if self.value is not None and not isfinite(self.value):
            raise ValueError("value must be finite")
        return self


class PatientLabSampleCreate(_MedicalWriteModel):
    sample_type: str = Field(min_length=1)
    date: AwareDatetime
    values: list[PatientLabValueCreate] = Field(
        default_factory=lambda: list[PatientLabValueCreate]()
    )

    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, value: object) -> object:
        return _parse_aware_datetime(value)


class PatientMedicationCreate(_MedicalWriteModel):
    medication: str = Field(min_length=1)
    medication_indication: str | None = Field(default=None, min_length=1)
    intake_times: list[str] = Field(default_factory=list)
    unit: str | None = Field(default=None, min_length=1)
    dosage: JsonValue = None
    active: bool = True

    @field_validator("intake_times")
    @classmethod
    def validate_intake_times(cls, values: list[str]) -> list[str]:
        return _validate_references(values)


class PatientMedicationUpdate(_MedicalWriteModel):
    medication: str | None = Field(default=None, min_length=1)
    medication_indication: str | None = Field(default=None, min_length=1)
    intake_times: list[str] | None = None
    unit: str | None = Field(default=None, min_length=1)
    dosage: JsonValue = None
    active: bool | None = None

    @field_validator("intake_times")
    @classmethod
    def validate_intake_times(cls, values: list[str] | None) -> list[str] | None:
        return None if values is None else _validate_references(values)

    @model_validator(mode="after")
    def validate_update(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("at least one medication field must be provided")
        non_nullable = {"medication", "intake_times", "active"}
        null_fields = {
            field_name
            for field_name in self.model_fields_set & non_nullable
            if getattr(self, field_name) is None
        }
        if null_fields:
            raise ValueError(
                f"{', '.join(sorted(null_fields))} must not be null when provided"
            )
        return self


class PatientMedicationScheduleCreate(_MedicalWriteModel):
    medication_ids: list[int] = Field(default_factory=lambda: list[int]())

    @field_validator("medication_ids")
    @classmethod
    def validate_medication_ids(cls, values: list[int]) -> list[int]:
        return _validate_ids(values)


class PatientMedicationScheduleUpdate(_MedicalWriteModel):
    medication_ids: list[int]

    @field_validator("medication_ids")
    @classmethod
    def validate_medication_ids(cls, values: list[int]) -> list[int]:
        return _validate_ids(values)


class PatientMedicationScheduleAggregateCreate(_MedicalWriteModel):
    medication_indices: list[int] = Field(default_factory=lambda: list[int]())

    @field_validator("medication_indices")
    @classmethod
    def validate_medication_indices(cls, values: list[int]) -> list[int]:
        if any(value < 0 for value in values):
            raise ValueError("medication indices must be non-negative")
        if len(values) != len(set(values)):
            raise ValueError("medication indices must be unique")
        return values


class PatientMedicalLedgerCreate(_MedicalWriteModel):
    patient: str = Field(min_length=1)
    diseases: list[PatientDiseaseCreate] = Field(
        default_factory=lambda: list[PatientDiseaseCreate]()
    )
    events: list[PatientEventCreate] = Field(
        default_factory=lambda: list[PatientEventCreate]()
    )
    lab_samples: list[PatientLabSampleCreate] = Field(
        default_factory=lambda: list[PatientLabSampleCreate]()
    )
    lab_values: list[PatientLabValueCreate] = Field(
        default_factory=lambda: list[PatientLabValueCreate]()
    )
    medications: list[PatientMedicationCreate] = Field(
        default_factory=lambda: list[PatientMedicationCreate]()
    )
    medication_schedules: list[PatientMedicationScheduleAggregateCreate] = Field(
        default_factory=lambda: list[PatientMedicationScheduleAggregateCreate]()
    )

    @model_validator(mode="after")
    def validate_schedule_indices(self) -> Self:
        medication_count = len(self.medications)
        if any(
            index >= medication_count
            for schedule in self.medication_schedules
            for index in schedule.medication_indices
        ):
            raise ValueError("medication schedule index is out of range")
        return self


__all__ = [
    "PatientDiseaseCreate",
    "PatientEventCreate",
    "PatientLabSampleCreate",
    "PatientLabValueCreate",
    "PatientMedicalLedgerCreate",
    "PatientMedicationCreate",
    "PatientMedicationScheduleAggregateCreate",
    "PatientMedicationScheduleCreate",
    "PatientMedicationScheduleUpdate",
    "PatientMedicationUpdate",
]
