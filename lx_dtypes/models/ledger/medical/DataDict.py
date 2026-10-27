from __future__ import annotations

from datetime import date, datetime
from typing import Literal, NotRequired, TypedDict

from lx_dtypes.models.base.app_base_model.ddict.LedgerBaseModelDataDict import (
    LedgerBaseModelDataDict,
)
from lx_dtypes.models.contracts.json_types import JsonObject, JsonValue


class NormalRangeDataDict(TypedDict):
    min: NotRequired[float | None]
    max: NotRequired[float | None]
    male: NotRequired[NormalRangeBandDataDict | None]
    female: NotRequired[NormalRangeBandDataDict | None]
    other: NotRequired[NormalRangeBandDataDict | None]


class NormalRangeBandDataDict(TypedDict):
    min: NotRequired[float | None]
    max: NotRequired[float | None]


class PatientDiseaseDataDict(LedgerBaseModelDataDict):
    patient: str
    disease: str
    classification_choices: list[str]
    start_date: date | None
    end_date: date | None
    numerical_descriptors: JsonObject
    subcategories: JsonObject
    last_update: datetime | None


class PatientEventDataDict(LedgerBaseModelDataDict):
    patient: str
    event: str
    date_start: date
    date_end: date | None
    description: str | None
    classification_choice: str | None
    subcategories: JsonObject
    numerical_descriptors: JsonObject
    last_update: datetime | None


class PatientLabValueDataDict(LedgerBaseModelDataDict):
    patient: str | None
    lab_value: str
    value: float | None
    value_str: str | None
    sample: str | None
    timestamp: datetime
    normal_range: NormalRangeDataDict
    unit: str | None


class PatientLabSampleDataDict(LedgerBaseModelDataDict):
    patient: str
    sample_type: str
    date: datetime
    values: list[PatientLabValueDataDict]


class SerializedPatientLabSampleDataDict(LedgerBaseModelDataDict):
    patient: str
    sample_type: str
    date: datetime
    values: str


class MedicationSubstanceDataDict(TypedDict):
    name: str
    strength: NotRequired[str | None]


class MedicationDosingScheduleDataDict(TypedDict):
    morning: NotRequired[str | None]
    noon: NotRequired[str | None]
    evening: NotRequired[str | None]
    night: NotRequired[str | None]
    weekday: NotRequired[int | None]
    free_text: NotRequired[str | None]


class MedicationScheduleHeadingDataDict(TypedDict):
    code: NotRequired[int | None]
    text: NotRequired[str | None]


class MedicationScheduleFreeTextLineDataDict(TypedDict):
    text: str


class MedicationScheduleCompoundEntryDataDict(TypedDict):
    text: str
    bound_note: NotRequired[str | None]


class PatientMedicationDataDict(LedgerBaseModelDataDict):
    start_at: NotRequired[datetime | None]
    end_at: NotRequired[datetime | None]
    patient: str
    dosage: JsonValue
    intake_times: list[str]
    medication: str | None
    medication_indication: str | None
    pzn: str | None
    substances: list[MedicationSubstanceDataDict]
    dosing: MedicationDosingScheduleDataDict
    dosage_form: str | None
    dosage_form_code: str | None
    unit: str | None
    unit_code: str | None
    notes: str | None
    bound_note: str | None
    active: bool


class MedicationScheduleMedicationRowDataDict(TypedDict):
    kind: Literal["medication"]
    medication: PatientMedicationDataDict


class MedicationScheduleCompoundRowDataDict(TypedDict):
    kind: Literal["compound"]
    entry: MedicationScheduleCompoundEntryDataDict


class MedicationScheduleFreeTextRowDataDict(TypedDict):
    kind: Literal["free_text"]
    entry: MedicationScheduleFreeTextLineDataDict


type MedicationScheduleRowDataDict = (
    MedicationScheduleMedicationRowDataDict
    | MedicationScheduleCompoundRowDataDict
    | MedicationScheduleFreeTextRowDataDict
)


class MedicationScheduleBlockDataDict(TypedDict):
    heading: NotRequired[MedicationScheduleHeadingDataDict | None]
    rows: list[MedicationScheduleRowDataDict]


class PatientMedicationScheduleDataDict(LedgerBaseModelDataDict):
    patient: str
    medications: list[PatientMedicationDataDict]
    medication_blocks: list[MedicationScheduleBlockDataDict]
    schedule_created_at: datetime
    updated_at: datetime


class SerializedPatientMedicationScheduleDataDict(LedgerBaseModelDataDict):
    patient: str
    medications: str
    medication_blocks: str
    schedule_created_at: datetime
    updated_at: datetime


class PatientMedicalLedgerDataDict(LedgerBaseModelDataDict):
    patient: str
    diseases: list[PatientDiseaseDataDict]
    events: list[PatientEventDataDict]
    lab_samples: list[PatientLabSampleDataDict]
    lab_values: list[PatientLabValueDataDict]
    medications: list[PatientMedicationDataDict]
    medication_schedules: list[PatientMedicationScheduleDataDict]


class SerializedPatientMedicalLedgerDataDict(LedgerBaseModelDataDict):
    patient: str
    diseases: str
    events: str
    lab_samples: str
    lab_values: str
    medications: str
    medication_schedules: str
