from typing import Dict

from pydantic import Field

from lx_dtypes.models.patient.patient import Patient
from lx_dtypes.utils.mixins.base_model import AppBaseModel

from .patient_examination import PatientExamination


class PatientLedger(AppBaseModel):
    """Ledger to manage patients and their examinations."""

    patients: Dict[str, Patient] = Field(default_factory=dict)
    examinations: Dict[str, PatientExamination] = Field(default_factory=dict)

    def add_patient(self, patient: Patient):
        self.patients[patient.uuid] = patient

    def get_patient_by_uuid(self, patient_uuid: str) -> Patient:
        patient = self.patients.get(patient_uuid)
        assert patient is not None, f"Patient with UUID {patient_uuid} not found."
        return patient

    def get_examination_by_uuid(self, examination_uuid: str) -> PatientExamination:
        examination = self.examinations.get(examination_uuid)
        assert examination is not None, (
            f"Examination with UUID {examination_uuid} not found."
        )
        return examination

    def add_patient_examination(self, examination: PatientExamination):
        patient_uuid = examination.patient_uuid
        if not self._patient_exists(patient_uuid):
            raise ValueError(
                f"Patient with UUID {patient_uuid} does not exist in the ledger."
            )

        self.examinations[examination.uuid] = examination

    def _patient_exists(self, patient_uuid: str) -> bool:
        patient = self.patients.get(patient_uuid)
        if patient is None:
            return False
        return True

    def _examination_exists(self, examination_uuid: str) -> bool:
        examination = self.examinations.get(examination_uuid)
        if examination is None:
            return False
        return True
