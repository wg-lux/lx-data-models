from datetime import date
from typing import Dict, List, Optional, Set, Tuple
from uuid import uuid4

from pydantic import Field

from lx_dtypes.models.patient.patient import Patient, PatientDataDict
from lx_dtypes.models.patient.patient_ledger import PatientLedger
from lx_dtypes.models.patient_interface.main import PatientInterface
from lx_dtypes.utils.mixins.base_model import AppBaseModel

from .import_exams import (
    load_smartie_exams_csv,
    smartie_exams_to_ledger,
    smartie_findings_exams_to_ledger,
    smartie_patients_to_ledger,
)


def int_str_dict_factory() -> dict[int, str]:
    return {}


class SmartieExaminations(AppBaseModel):
    examinations: List["SmartieExaminationSchema"]
    exam_id2uuid: Optional[dict[int, str]] = Field(default_factory=int_str_dict_factory)
    record_id2uuid: Optional[dict[int, str]] = Field(
        default_factory=int_str_dict_factory
    )
    person_id2uuid: Optional[dict[int, str]] = Field(
        default_factory=int_str_dict_factory
    )

    def initialize_mappings(self) -> None:
        # check if already initialized
        if self.record_id2uuid and self.person_id2uuid:
            return

        # exam_ids: Set[int] = set()
        record_ids: Set[int] = set()
        person_ids: Set[int] = set()
        for exam in self.examinations:
            # exam_ids.add(exam.exam_id)
            record_ids.add(exam.record_id)
            person_ids.add(exam.person_id)

        record_id2uuid: Dict[int, str] = {rid: str(uuid4()) for rid in record_ids}
        person_id2uuid: Dict[int, str] = {pid: str(uuid4()) for pid in person_ids}

        # self.exam_id2uuid = exam_id2uuid
        self.record_id2uuid = record_id2uuid
        self.person_id2uuid = person_id2uuid

    def validate_record_ids_unique(self) -> None:
        record_ids = [exam.record_id for exam in self.examinations]
        if len(record_ids) != len(set(record_ids)):
            duplicates = set([x for x in record_ids if record_ids.count(x) > 1])
            raise ValueError(
                f"Duplicate record_ids found in examinations: {duplicates}"
            )

    def create_ledger(self, name: str = "SmartieExaminations") -> "PatientLedger":
        self.initialize_mappings()
        # self.validate_exam_ids_unique()
        self.validate_record_ids_unique()

        ledger = PatientLedger.model_construct(
            name=name,
        )
        person_id2uuid = self.person_id2uuid
        assert person_id2uuid is not None

        smartie_patients_to_ledger(
            exams=self.examinations,
            ledger=ledger,
            person_id2uuid=person_id2uuid,
        )

        record_id2uuid = self.record_id2uuid
        assert record_id2uuid is not None

        smartie_exams_to_ledger(
            exams=self.examinations,
            ledger=ledger,
            person_id2uuid=person_id2uuid,
            record_id2uuid=record_id2uuid,
        )

        return ledger

    def _validate_interface_integrity(
        self, patient_interface: PatientInterface
    ) -> None:
        ledger = patient_interface.patient_ledger

        person_id2uuid = self.person_id2uuid
        assert person_id2uuid is not None
        for _person_id, patient_uuid in person_id2uuid.items():
            _ = ledger.get_patient_by_uuid(patient_uuid)
        record_id2uuid = self.record_id2uuid
        assert record_id2uuid is not None
        for _record_id, examination_uuid in record_id2uuid.items():
            _ = ledger.get_examination_by_uuid(examination_uuid)

    def export_exam_findings_to_interface(
        self, patient_interface: PatientInterface
    ) -> None:
        """Add findings to examinations in the ledger using a generic patient interface.

        Args:
            patient_interface (PatientInterface): The patient interface to interact with the ledger.
        """
        self._validate_interface_integrity(patient_interface)

        person_id2uuid = self.person_id2uuid
        assert person_id2uuid is not None
        record_id2uuid = self.record_id2uuid
        assert record_id2uuid is not None

        smartie_findings_exams_to_ledger(
            exams=self.examinations,
            patient_interface=patient_interface,
            person_id2uuid=person_id2uuid,
            record_id2uuid=record_id2uuid,
        )


class SmartieExaminationSchema(AppBaseModel):
    record_id: int
    person_id: int
    gender: int
    birthdate: date  # provided as string, example "01.01.1961  00:00:00"
    ai: bool  # provided as bool
    study_number: str
    center: str
    number: int
    examiner: str = Field(default="unknown")
    exam_id: int = Field(default=-1)
    withdrawal_time: Optional[int] = None  # in minutes, on import replace -1 with None
    sedation: List[str] = Field(
        default_factory=list
    )  # provided as string like "{propofol,midazolam}"
    bbps_worst: Optional[int] = None  # on import replace -1 with None
    bbps_total: Optional[int] = None  # on import replace -1 with None
    indication: str = Field(default="unknown")
    indication_rev: str = Field(default="unknown")
    std_indication: str = Field(default="unknown")
    deepest_point_reached: str = Field(default="unknown")
    reason_cecum_not_reached: Optional[str] = None
    bbps: Optional[Tuple[int, int, int]] = None  # provided as string like "{2,3,3}"
    exam_date: date  # provided as string, example "23.02.2022"
    processor: str

    @classmethod
    def load_csv(cls, filepath: str) -> SmartieExaminations:
        smartie_examinations = load_smartie_exams_csv(filepath)
        return smartie_examinations

    def create_patient(self, new_uuid: Optional[str] = None) -> Tuple[str, Patient]:
        if not new_uuid:
            new_uuid = str(uuid4())
        if self.gender == 1:
            gender = "female"
        elif self.gender == 0:
            gender = "male"
        else:
            raise ValueError(f"Invalid gender value: {self.gender}")

        external_ids: Dict[str, str] = {
            "smartie_person_id": str(self.person_id),
            "smartie_record_id": str(self.record_id),
        }

        patient_dict = PatientDataDict(
            first_name="unknown",
            last_name="unknown",
            dob=self.birthdate,
            center_name=self.center,
            gender=gender,
            external_ids=external_ids,
            uuid=new_uuid,
        )

        patient = Patient.model_validate(patient_dict)
        # Placeholder for actual implementation
        return new_uuid, patient
