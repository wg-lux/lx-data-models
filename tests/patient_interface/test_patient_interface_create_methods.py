from typing import Tuple

from lx_dtypes.models.ledger.patient_examination import PatientExamination
from lx_dtypes.models.ledger.patient_finding import PatientFinding
from lx_dtypes.models.patient_interface import PatientInterface


class TestPatientInterfaceCreateMethods:
    def test_patient_interface_create_patient_examination(
        self,
        sample_patient_interface: PatientInterface,
        sample_patient_ledger_patient_uuid: str,
        examination_name_colonoscopy: str,
    ):
        examination = sample_patient_interface.create_patient_examination(
            patient_uuid=sample_patient_ledger_patient_uuid,
            examination_name=examination_name_colonoscopy,
        )
        assert examination.patient_uuid == sample_patient_ledger_patient_uuid
        assert examination.examination_name == examination_name_colonoscopy
        assert examination.examination_template is None

    def test_patient_interface_create_examination_finding(
        self,
        sample_patient_examination: Tuple[PatientExamination, PatientInterface],
        finding_name_colon_polyp: str,
    ):
        patient_examination, sample_patient_interface = sample_patient_examination
        sample_patient_interface.create_examination_finding(
            examination_uuid=patient_examination.uuid,
            finding_name=finding_name_colon_polyp,
        )
        findings_names = [
            finding.finding_name for finding in patient_examination.findings
        ]
        assert finding_name_colon_polyp in findings_names

    def test_patient_finding_get_or_create_classifications(
        self,
        sample_patient_finding_colon_polyp: Tuple[PatientFinding, PatientInterface],
    ):
        finding, _sample_patient_interface = sample_patient_finding_colon_polyp
        classifications = finding.classifications
        assert classifications is not None
        assert classifications.patient_finding_uuid == finding.uuid
        assert (
            classifications.patient_examination_uuid == finding.patient_examination_uuid
        )
        assert classifications.patient_uuid == finding.patient_uuid

    def test_patient_interface_create_patient_examination_raises(
        self,
        sample_patient_interface: PatientInterface,
        sample_patient_ledger_patient_uuid: str,
    ):
        invalid_examination_name = "NonExistentExamination"
        try:
            sample_patient_interface.create_patient_examination(
                patient_uuid=sample_patient_ledger_patient_uuid,
                examination_name=invalid_examination_name,
            )
        except ValueError as e:
            assert (
                str(e)
                == f"Examination '{invalid_examination_name}' does not exist in the knowledge base."
            )

    def test_patient_interface_create_examination_finding_raises(
        self,
        sample_patient_examination: Tuple[PatientExamination, PatientInterface],
    ):
        patient_examination, sample_patient_interface = sample_patient_examination
        invalid_finding_name = "NonExistentFinding"
        try:
            sample_patient_interface.create_examination_finding(
                examination_uuid=patient_examination.uuid,
                finding_name=invalid_finding_name,
            )
        except ValueError as e:
            assert (
                str(e)
                == f"Finding '{invalid_finding_name}' does not exist in the knowledge base."
            )
