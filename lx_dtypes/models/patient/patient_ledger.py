from typing import TYPE_CHECKING, Any, Dict, List

from pydantic import Field, field_serializer

from lx_dtypes.models.core.center import Center
from lx_dtypes.models.examiner.examiner import Examiner
from lx_dtypes.models.patient.patient import Patient
from lx_dtypes.utils.mixins.base_model import AppBaseModel

from .patient_examination import PatientExamination

if TYPE_CHECKING:  # pragma: no cover
    from lx_dtypes.models.examiner.examiner import Examiner, ExaminerDataDict


class PatientLedger(AppBaseModel):
    """Ledger to manage patients and their examinations."""

    patients: Dict[str, Patient] = Field(default_factory=dict)
    examinations: Dict[str, PatientExamination] = Field(default_factory=dict)
    centers: Dict[str, Center] = Field(default_factory=dict)

    @field_serializer("patients")
    def serialize_patients(self, patients: Dict[str, Patient]) -> Dict[str, Any]:
        r: Dict[str, Any] = {
            patient_uuid: patient.model_dump()
            for patient_uuid, patient in patients.items()
        }
        return r

    @field_serializer("examinations")
    def serialize_examinations(
        self, examinations: Dict[str, PatientExamination]
    ) -> Dict[str, Any]:
        r: Dict[str, Any] = {
            exam_uuid: exam.model_dump() for exam_uuid, exam in examinations.items()
        }
        return r

    @field_serializer("centers")
    def serialize_centers(self, centers: Dict[str, Center]) -> Dict[str, Any]:
        r: Dict[str, Any] = {
            center_uuid: center.model_dump() for center_uuid, center in centers.items()
        }
        return r

    def add_patient(self, patient: Patient) -> None:
        self.patients[patient.uuid] = patient

    def add_examiner(self, center_uuid: str, examiner_dict: "ExaminerDataDict") -> None:
        center_name = examiner_dict["center_name"]

        if not self._center_exists(center_uuid):
            center = Center(name=center_name, uuid=center_uuid)
            self.centers[center_uuid] = center

        _examiner = Examiner.model_validate(examiner_dict)
        self.centers[center_uuid].examiners[_examiner.uuid] = _examiner
        return

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

    def get_center_by_uuid(self, center_uuid: str) -> Center:
        center = self.centers.get(center_uuid)
        assert center is not None, f"Center with UUID {center_uuid} not found."
        return center

    def get_center_by_name(self, center_name: str) -> Center:
        center = next((c for c in self.centers.values() if c.name == center_name), None)
        assert center is not None, f"Center with name {center_name} not found."
        return center

    def get_examinations_by_patient_uuid(
        self, patient_uuid: str
    ) -> Dict[str, PatientExamination]:
        examinations = {
            uuid: exam
            for uuid, exam in self.examinations.items()
            if exam.patient_uuid == patient_uuid
        }
        return examinations

    def get_examination_uuids_by_patient_uuid(self, patient_uuid: str) -> List[str]:
        examination_uuids = [
            exam.uuid
            for exam in self.examinations.values()
            if exam.patient_uuid == patient_uuid
        ]
        return examination_uuids

    def add_patient_examination(self, examination: PatientExamination) -> None:
        patient_uuid = examination.patient_uuid
        if not self._patient_exists(patient_uuid):
            raise ValueError(
                f"Patient with UUID {patient_uuid} does not exist in the ledger."
            )

        self.examinations[examination.uuid] = examination

    def delete_patient_examination(self, examination_uuid: str) -> None:
        if not self._examination_exists(examination_uuid):
            raise ValueError(
                f"Examination with UUID {examination_uuid} does not exist in the ledger."
            )

        del self.examinations[examination_uuid]

    def delete_patient(self, patient_uuid: str) -> None:
        if not self._patient_exists(patient_uuid):
            raise ValueError(
                f"Patient with UUID {patient_uuid} does not exist in the ledger."
            )

        examinations_to_delete = self.get_examination_uuids_by_patient_uuid(
            patient_uuid
        )
        for exam_uuid in examinations_to_delete:
            self.delete_patient_examination(exam_uuid)

        self.patients.pop(patient_uuid)

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

    def _center_exists(self, center_uuid: str) -> bool:
        center = self.centers.get(center_uuid)
        if center is None:
            return False
        return True

    def _center_exists_by_name(self, center_name: str) -> bool:
        center = next((c for c in self.centers.values() if c.name == center_name), None)
        if center is None:
            return False
        return True
