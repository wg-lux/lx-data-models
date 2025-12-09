from typing import Tuple

from lx_dtypes.models.patient.patient import Patient
from lx_dtypes.models.patient.patient_examination import PatientExamination
from lx_dtypes.models.patient.patient_finding import PatientFinding
from lx_dtypes.models.patient_interface import PatientInterface


class TestPatientInterfaceModel:
    def test_patient_interface_model(
        self,
        sample_patient_interface: PatientInterface,
        sample_patient: Patient,
        sample_patient_ledger_patient_uuid: str,
    ):
        ledger = sample_patient_interface.patient_ledger
        uuid = sample_patient_ledger_patient_uuid
        assert uuid in ledger.patients
        assert ledger.patients[uuid] == sample_patient

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

    def test_patient_interface_get_patient_examination_by_uuid(
        self,
        sample_patient_examination: Tuple[PatientExamination, PatientInterface],
    ):
        patient_examination, sample_patient_interface = sample_patient_examination
        examination = sample_patient_interface.get_patient_examination_by_uuid(
            patient_examination.uuid
        )
        assert examination == patient_examination

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

    def test_patient_interface_add_classification_choice_to_finding(
        self,
        sample_patient_finding_colon_polyp: Tuple[PatientFinding, PatientInterface],
        classification_choice_name_lesion_size_oval_mm: str,
        classification_name_lesion_size_mm: str,
    ):
        patient_finding, patient_interface = sample_patient_finding_colon_polyp
        examination_id = patient_finding.patient_examination_uuid
        assert examination_id is not None

        patient_interface.add_classification_choice_to_finding(
            examination_uuid=examination_id,
            finding_uuid=patient_finding.uuid,
            classification_name=classification_name_lesion_size_mm,
            choice_name=classification_choice_name_lesion_size_oval_mm,
        )

        examination = patient_interface.get_patient_examination_by_uuid(examination_id)
        finding = examination.get_finding_by_uuid(patient_finding.uuid)
        classifications = finding.get_or_create_classifications()
        choice_names = [choice.name for choice in classifications.choices]
        assert classification_choice_name_lesion_size_oval_mm in choice_names

    def test_patient_interface_add_invalid_classification_choice_to_finding_raises(
        self,
        sample_patient_finding_colon_polyp: Tuple[PatientFinding, PatientInterface],
    ):
        patient_finding, patient_interface = sample_patient_finding_colon_polyp
        examination_id = patient_finding.patient_examination_uuid
        assert examination_id is not None

        invalid_classification_name = "NonExistentClassification"
        invalid_choice_name = "NonExistentChoice"

        try:
            patient_interface.add_classification_choice_to_finding(
                examination_uuid=examination_id,
                finding_uuid=patient_finding.uuid,
                classification_name=invalid_classification_name,
                choice_name=invalid_choice_name,
            )
        except ValueError as e:
            assert (
                str(e)
                == f"Classification '{invalid_classification_name}' does not exist in the knowledge base."
            )
        else:
            assert False, "Expected ValueError was not raised."

    def test_patient_interface_add_invalid_choice_to_finding_raises(
        self,
        sample_patient_finding_colon_polyp: Tuple[PatientFinding, PatientInterface],
        classification_name_lesion_size_mm: str,
    ):
        patient_finding, patient_interface = sample_patient_finding_colon_polyp
        examination_id = patient_finding.patient_examination_uuid
        assert examination_id is not None

        invalid_choice_name = "NonExistentChoice"

        try:
            patient_interface.add_classification_choice_to_finding(
                examination_uuid=examination_id,
                finding_uuid=patient_finding.uuid,
                classification_name=classification_name_lesion_size_mm,
                choice_name=invalid_choice_name,
            )
        except ValueError as e:
            assert (
                str(e)
                == f"Classification choice '{invalid_choice_name}' does not exist in the knowledge base."
            )
        else:
            assert False, "Expected ValueError was not raised."

    def test_patient_interface_add_choice_not_in_valid_choices_raises(
        self,
        sample_patient_finding_colon_polyp: Tuple[PatientFinding, PatientInterface],
        classification_name_lesion_size_mm: str,
        classification_choice_name_paris_1s: str,
    ):
        patient_finding, patient_interface = sample_patient_finding_colon_polyp
        examination_id = patient_finding.patient_examination_uuid
        assert examination_id is not None

        invalid_choice_name = classification_choice_name_paris_1s

        try:
            patient_interface.add_classification_choice_to_finding(
                examination_uuid=examination_id,
                finding_uuid=patient_finding.uuid,
                classification_name=classification_name_lesion_size_mm,
                choice_name=invalid_choice_name,
            )
        except ValueError as e:
            classification_object = patient_interface.knowledge_base.get_classification(
                classification_name_lesion_size_mm
            )
            valid_choices = classification_object.choice_names
            assert str(e) == (
                f"Choice '{invalid_choice_name}' is not a valid choice for classification "
                f"'{classification_name_lesion_size_mm}'. Valid choices are: {valid_choices}"
            )
        else:
            assert False, "Expected ValueError was not raised."
