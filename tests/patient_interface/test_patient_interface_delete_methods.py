from typing import Tuple

from lx_dtypes.models.patient.patient_finding import PatientFinding
from lx_dtypes.models.patient.patient_finding_classification_choice import (
    PatientFindingClassificationChoice,
)
from lx_dtypes.models.patient_interface import PatientInterface


class TestPatientInterfaceDeleteMethods:
    def test_patient_interface_pe_delete_finding(
        self,
        sample_patient_finding_colon_polyp: Tuple[PatientFinding, PatientInterface],
    ):
        patient_finding, patient_interface = sample_patient_finding_colon_polyp
        examination_id = patient_finding.patient_examination_uuid
        assert examination_id is not None

        examination = patient_interface.get_patient_examination_by_uuid(examination_id)
        examination.delete_finding(patient_finding.uuid)

        finding_uuids = [finding.uuid for finding in examination.findings]
        assert patient_finding.uuid not in finding_uuids

    def test_patient_interface_delete_patient(
        self,
        sample_patient_finding_colon_polyp: Tuple[PatientFinding, PatientInterface],
        sample_patient_ledger_patient_uuid: str,
    ):
        _patient_finding, sample_patient_interface = sample_patient_finding_colon_polyp
        patient_interface = sample_patient_interface
        patient_uuid = sample_patient_ledger_patient_uuid

        patient_interface.patient_ledger.delete_patient(patient_uuid)

        assert patient_uuid not in patient_interface.patient_ledger.patients

    def test_patient_interface_pf_delete_classification_choice(
        self,
        sample_patient_finding_with_classification_choice: Tuple[
            PatientFindingClassificationChoice, PatientFinding, PatientInterface
        ],
    ):
        (
            classification_choice,
            patient_finding,
            patient_interface,
        ) = sample_patient_finding_with_classification_choice
        examination_id = patient_finding.patient_examination_uuid
        assert examination_id is not None

        finding = patient_interface.get_patient_finding_by_patient_examination_and_finding_uuid(
            examination_uuid=examination_id,
            finding_uuid=patient_finding.uuid,
        )
        finding.delete_classification_choice(classification_choice.uuid)

        classifications = finding.get_or_create_classifications()
        choice_uuids = [choice.uuid for choice in classifications.choices]
        assert classification_choice.uuid not in choice_uuids

    def test_patient_interface_delete_indication_from_examination(
        self,
        sample_patient_examination: Tuple[PatientFinding, PatientInterface],
        examination_name_colonoscopy: str,
        indication_name_screening_colonoscopy: str,
    ):
        patient_examination, patient_interface = sample_patient_examination
        examination_id = patient_examination.uuid

        # First, add an indication to the examination
        patient_interface.add_indication_to_examination(
            examination_uuid=examination_id,
            indication_name=indication_name_screening_colonoscopy,
        )

        # Retrieve the indication UUID
        examination = patient_interface.get_patient_examination_by_uuid(examination_id)
        indications = examination.indications
        indication_uuids = [
            indication.uuid
            for indication in indications
            if indication.indication_name == indication_name_screening_colonoscopy
        ]
        assert len(indication_uuids) == 1
        indication_uuid = indication_uuids[0]

        # Now, delete the indication
        patient_interface.delete_indication_from_examination(
            examination_uuid=examination_id,
            indication_uuid=indication_uuid,
        )

        # Verify the indication has been deleted
        examination = patient_interface.get_patient_examination_by_uuid(examination_id)
        indications = examination.indications
        remaining_indication_uuids = [indication.uuid for indication in indications]
        assert indication_uuid not in remaining_indication_uuids
