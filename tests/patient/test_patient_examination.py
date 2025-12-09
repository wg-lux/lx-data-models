from typing import Tuple

from lx_dtypes.models.patient.patient_examination import PatientExamination
from lx_dtypes.models.patient_interface import PatientInterface


class TestPatientExamination:
    def test_create_patient_examination(
        self,
        examination_name_colonoscopy: str,
        sample_patient_examination: Tuple[PatientExamination, PatientInterface],
        sample_patient_ledger_patient_uuid: str,
    ):
        patient_examination, _patient_interface = sample_patient_examination
        assert patient_examination.patient_uuid == sample_patient_ledger_patient_uuid
        assert patient_examination.examination_name == examination_name_colonoscopy
        assert patient_examination.examination_template is None
