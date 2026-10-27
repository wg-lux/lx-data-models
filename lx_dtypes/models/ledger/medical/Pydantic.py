from __future__ import annotations

from datetime import date
from typing import Annotated, Literal, Self, cast

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from lx_dtypes.models.base.app_base_model.pydantic.LedgerBaseModel import (
    LedgerBaseModel,
)
from lx_dtypes.models.contracts.json_types import JsonObject
from lx_dtypes.models.contracts.lab_value import LabValueNormalRangeData
from lx_dtypes.models.contracts.medication import (
    MedicationEntryFields,
    MedicationPeriodFields,
    MedicationScheduleCompoundEntry,
    MedicationScheduleFreeTextLine,
    MedicationScheduleHeading,
)

from .DataDict import (
    PatientDiseaseDataDict,
    PatientEventDataDict,
    PatientLabSampleDataDict,
    PatientLabValueDataDict,
    PatientMedicalLedgerDataDict,
    PatientMedicationDataDict,
    PatientMedicationScheduleDataDict,
    SerializedPatientLabSampleDataDict,
    SerializedPatientMedicalLedgerDataDict,
    SerializedPatientMedicationScheduleDataDict,
)


class _MedicalLedgerModel:
    @classmethod
    def list_type_fields(cls) -> list[str]:
        return ["tags"]

    @classmethod
    def nested_fields(cls) -> list[str]:
        return []


class PatientDisease(_MedicalLedgerModel, LedgerBaseModel[PatientDiseaseDataDict]):
    patient: str
    disease: str
    classification_choices: list[str] = Field(default_factory=list)
    start_date: date | None = None
    end_date: date | None = None
    numerical_descriptors: JsonObject = Field(default_factory=dict)
    subcategories: JsonObject = Field(default_factory=dict)
    last_update: AwareDatetime | None = None

    @property
    def ddict_class(self) -> type[PatientDiseaseDataDict]:
        return PatientDiseaseDataDict


class PatientEvent(_MedicalLedgerModel, LedgerBaseModel[PatientEventDataDict]):
    patient: str
    event: str
    date_start: date
    date_end: date | None = None
    description: str | None = None
    classification_choice: str | None = None
    subcategories: JsonObject = Field(default_factory=dict)
    numerical_descriptors: JsonObject = Field(default_factory=dict)
    last_update: AwareDatetime | None = None

    @property
    def ddict_class(self) -> type[PatientEventDataDict]:
        return PatientEventDataDict


class PatientLabValue(_MedicalLedgerModel, LedgerBaseModel[PatientLabValueDataDict]):
    patient: str | None = None
    lab_value: str
    value: float | None = None
    value_str: str | None = None
    sample: str | None = None
    timestamp: AwareDatetime
    normal_range: LabValueNormalRangeData = Field(
        default_factory=LabValueNormalRangeData
    )
    unit: str | None = None

    @property
    def ddict_class(self) -> type[PatientLabValueDataDict]:
        return PatientLabValueDataDict


class PatientLabSample(_MedicalLedgerModel, LedgerBaseModel[PatientLabSampleDataDict]):
    patient: str
    sample_type: str
    date: AwareDatetime
    values: list[PatientLabValue] = Field(default_factory=list)

    @property
    def ddict_class(self) -> type[PatientLabSampleDataDict]:
        return PatientLabSampleDataDict

    @classmethod
    def nested_fields(cls) -> list[str]:
        return ["values"]

    @property
    def serialized_ddict_class(self) -> type[SerializedPatientLabSampleDataDict]:
        return SerializedPatientLabSampleDataDict

    @classmethod
    def serialized_model_class(cls) -> type[SerializedPatientLabSample]:
        return SerializedPatientLabSample

    @property
    def serialized_model(self) -> SerializedPatientLabSample:
        return cast(SerializedPatientLabSample, super().serialized_model)


class SerializedPatientLabSample(
    _MedicalLedgerModel, LedgerBaseModel[SerializedPatientLabSampleDataDict]
):
    patient: str
    sample_type: str
    date: AwareDatetime
    values: str = ""

    @property
    def ddict_class(self) -> type[SerializedPatientLabSampleDataDict]:
        return SerializedPatientLabSampleDataDict


class PatientMedication(
    _MedicalLedgerModel,
    MedicationPeriodFields,
    MedicationEntryFields,
    LedgerBaseModel[PatientMedicationDataDict],
):
    patient: str
    active: bool = True

    @model_validator(mode="after")
    def validate_not_entirely_blank(self) -> Self:
        if self.is_entirely_blank():
            raise ValueError(
                "a medication entry must set at least one identifying or "
                "descriptive field"
            )
        return self

    @property
    def ddict_class(self) -> type[PatientMedicationDataDict]:
        return PatientMedicationDataDict


class MedicationScheduleMedicationRow(BaseModel):
    """A medication-table row backed by a full `PatientMedication` entry."""

    model_config = ConfigDict(extra="forbid", strict=True)

    kind: Literal["medication"] = "medication"
    medication: PatientMedication


class MedicationScheduleCompoundRow(BaseModel):
    """A medication-table row for a compounded preparation (Rezeptureintrag)."""

    model_config = ConfigDict(extra="forbid", strict=True)

    kind: Literal["compound"] = "compound"
    entry: MedicationScheduleCompoundEntry


class MedicationScheduleFreeTextRow(BaseModel):
    """A medication-table row holding an unattached free-text line (Freitextzeile)."""

    model_config = ConfigDict(extra="forbid", strict=True)

    kind: Literal["free_text"] = "free_text"
    entry: MedicationScheduleFreeTextLine


MedicationScheduleRow = Annotated[
    MedicationScheduleMedicationRow
    | MedicationScheduleCompoundRow
    | MedicationScheduleFreeTextRow,
    Field(discriminator="kind"),
]


class MedicationScheduleBlock(BaseModel):
    """An ordered, optionally headed group of medication-table rows (BMP block)."""

    model_config = ConfigDict(extra="forbid", strict=True)

    heading: MedicationScheduleHeading | None = None
    rows: list[MedicationScheduleRow] = Field(min_length=1, max_length=45)


class PatientMedicationSchedule(
    _MedicalLedgerModel, LedgerBaseModel[PatientMedicationScheduleDataDict]
):
    patient: str
    medication_blocks: list[MedicationScheduleBlock] = Field(default_factory=list)
    schedule_created_at: AwareDatetime
    updated_at: AwareDatetime

    @model_validator(mode="after")
    def validate_block_headings(self) -> Self:
        for index, block in enumerate(self.medication_blocks):
            if index > 0 and block.heading is None:
                raise ValueError(
                    "every medication block after the first must have a heading"
                )
        return self

    @property
    def ddict_class(self) -> type[PatientMedicationScheduleDataDict]:
        return PatientMedicationScheduleDataDict

    @classmethod
    def nested_fields(cls) -> list[str]:
        return ["medication_blocks"]

    @classmethod
    def json_encoded_fields(cls) -> list[str]:
        return ["medication_blocks"]

    @property
    def serialized_ddict_class(
        self,
    ) -> type[SerializedPatientMedicationScheduleDataDict]:
        return SerializedPatientMedicationScheduleDataDict

    @classmethod
    def serialized_model_class(
        cls,
    ) -> type[SerializedPatientMedicationSchedule]:
        return SerializedPatientMedicationSchedule

    @property
    def serialized_model(self) -> SerializedPatientMedicationSchedule:
        return cast(SerializedPatientMedicationSchedule, super().serialized_model)


class SerializedPatientMedicationSchedule(
    _MedicalLedgerModel,
    LedgerBaseModel[SerializedPatientMedicationScheduleDataDict],
):
    patient: str
    medication_blocks: str = ""
    schedule_created_at: AwareDatetime
    updated_at: AwareDatetime

    @property
    def ddict_class(
        self,
    ) -> type[SerializedPatientMedicationScheduleDataDict]:
        return SerializedPatientMedicationScheduleDataDict


class PatientMedicalLedger(
    _MedicalLedgerModel, LedgerBaseModel[PatientMedicalLedgerDataDict]
):
    patient: str
    diseases: list[PatientDisease] = Field(default_factory=list)
    events: list[PatientEvent] = Field(default_factory=list)
    lab_samples: list[PatientLabSample] = Field(default_factory=list)
    lab_values: list[PatientLabValue] = Field(default_factory=list)
    medications: list[PatientMedication] = Field(default_factory=list)
    medication_schedules: list[PatientMedicationSchedule] = Field(default_factory=list)

    @property
    def ddict_class(self) -> type[PatientMedicalLedgerDataDict]:
        return PatientMedicalLedgerDataDict

    @classmethod
    def nested_fields(cls) -> list[str]:
        return [
            "diseases",
            "events",
            "lab_samples",
            "lab_values",
            "medications",
            "medication_schedules",
        ]

    @property
    def serialized_ddict_class(
        self,
    ) -> type[SerializedPatientMedicalLedgerDataDict]:
        return SerializedPatientMedicalLedgerDataDict

    @classmethod
    def serialized_model_class(cls) -> type[SerializedPatientMedicalLedger]:
        return SerializedPatientMedicalLedger

    @property
    def serialized_model(self) -> SerializedPatientMedicalLedger:
        return cast(SerializedPatientMedicalLedger, super().serialized_model)


class SerializedPatientMedicalLedger(
    _MedicalLedgerModel, LedgerBaseModel[SerializedPatientMedicalLedgerDataDict]
):
    patient: str
    diseases: str = ""
    events: str = ""
    lab_samples: str = ""
    lab_values: str = ""
    medications: str = ""
    medication_schedules: str = ""

    @property
    def ddict_class(self) -> type[SerializedPatientMedicalLedgerDataDict]:
        return SerializedPatientMedicalLedgerDataDict
