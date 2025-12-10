from typing import Tuple

from lx_dtypes.models.patient.patient import Patient
from lx_dtypes.models.patient.patient_examination import PatientExamination
from lx_dtypes.models.patient.patient_finding import PatientFinding
from lx_dtypes.models.patient_interface import PatientInterface


class TestPatientInterfaceGetMethods:
    def test_patient_interface_get_patient_by_uuid(
        self,
        sample_patient_interface: PatientInterface,
        sample_patient: Patient,
        sample_patient_ledger_patient_uuid: str,
    ):
        patient = sample_patient_interface.get_patient_by_uuid(
            sample_patient_ledger_patient_uuid
        )
        assert patient == sample_patient

    def test_patient_interface_get_patient_examination_by_uuid(
        self,
        sample_patient_examination: Tuple[PatientExamination, PatientInterface],
    ):
        patient_examination, sample_patient_interface = sample_patient_examination
        examination = sample_patient_interface.get_patient_examination_by_uuid(
            patient_examination.uuid
        )
        assert examination == patient_examination

    def test_interface_get_pf_by_pe_and_f_uuid(
        self,
        sample_patient_finding_colon_polyp: Tuple[PatientFinding, PatientInterface],
    ):
        # First, create the finding
        finding, sample_patient_interface = sample_patient_finding_colon_polyp
        examination_uuid = finding.patient_examination_uuid
        assert examination_uuid is not None
        # Retrieve the finding UUID
        finding_uuid = finding.uuid
        # Now, use the interface method to get the finding by UUID
        retrieved_finding = sample_patient_interface.get_patient_finding_by_patient_examination_and_finding_uuid(
            examination_uuid=examination_uuid,
            finding_uuid=finding_uuid,
        )
        assert retrieved_finding == finding
