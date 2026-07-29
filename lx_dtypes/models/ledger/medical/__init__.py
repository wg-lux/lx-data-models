from typing import TypedDict, TypeAlias

from .adapters import (
    ENDOREG_DB_LEDGER_NAMESPACE,
    build_patient_medical_ledger,
    patient_disease_from_endoreg,
    patient_event_from_endoreg,
    patient_lab_sample_from_endoreg,
    patient_lab_value_from_endoreg,
    patient_medication_from_endoreg,
    patient_medication_schedule_from_endoreg,
)
from .DataDict import (
    PatientDiseaseDataDict,
    PatientEventDataDict,
    PatientLabSampleDataDict,
    PatientLabValueDataDict,
    PatientMedicalLedgerDataDict,
    PatientMedicationDataDict,
    PatientMedicationScheduleDataDict,
)
from .Pydantic import (
    PatientDisease,
    PatientEvent,
    PatientLabSample,
    PatientLabValue,
    PatientMedicalLedger,
    PatientMedication,
    PatientMedicationSchedule,
)


class LMedicalLookupType(TypedDict):
    PatientDisease: type[PatientDisease]
    PatientEvent: type[PatientEvent]
    PatientLabSample: type[PatientLabSample]
    PatientLabValue: type[PatientLabValue]
    PatientMedication: type[PatientMedication]
    PatientMedicationSchedule: type[PatientMedicationSchedule]
    PatientMedicalLedger: type[PatientMedicalLedger]


l_medical_lookup = LMedicalLookupType(
    PatientDisease=PatientDisease,
    PatientEvent=PatientEvent,
    PatientLabSample=PatientLabSample,
    PatientLabValue=PatientLabValue,
    PatientMedication=PatientMedication,
    PatientMedicationSchedule=PatientMedicationSchedule,
    PatientMedicalLedger=PatientMedicalLedger,
)

l_medical_models: TypeAlias = (
    PatientDisease
    | PatientEvent
    | PatientLabSample
    | PatientLabValue
    | PatientMedication
    | PatientMedicationSchedule
    | PatientMedicalLedger
)
l_medical_ddicts: TypeAlias = (
    PatientDiseaseDataDict
    | PatientEventDataDict
    | PatientLabSampleDataDict
    | PatientLabValueDataDict
    | PatientMedicationDataDict
    | PatientMedicationScheduleDataDict
    | PatientMedicalLedgerDataDict
)

__all__ = [
    "ENDOREG_DB_LEDGER_NAMESPACE",
    "LMedicalLookupType",
    "PatientDisease",
    "PatientDiseaseDataDict",
    "PatientEvent",
    "PatientEventDataDict",
    "PatientLabSample",
    "PatientLabSampleDataDict",
    "PatientLabValue",
    "PatientLabValueDataDict",
    "PatientMedicalLedger",
    "PatientMedicalLedgerDataDict",
    "PatientMedication",
    "PatientMedicationDataDict",
    "PatientMedicationSchedule",
    "PatientMedicationScheduleDataDict",
    "build_patient_medical_ledger",
    "l_medical_ddicts",
    "l_medical_lookup",
    "l_medical_models",
    "patient_disease_from_endoreg",
    "patient_event_from_endoreg",
    "patient_lab_sample_from_endoreg",
    "patient_lab_value_from_endoreg",
    "patient_medication_from_endoreg",
    "patient_medication_schedule_from_endoreg",
]
