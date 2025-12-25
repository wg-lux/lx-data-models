from typing import Tuple

from lx_dtypes.models.ledger.patient_examination import PatientExamination
from lx_dtypes.models.ledger.patient_finding import PatientFinding
from lx_dtypes.models.patient_interface import PatientInterface


class TestPatientInterfaceUpdateMethods:
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
        choice_names = [choice.choice_name for choice in classifications.choices]
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

    def test_patient_interface_pe_add_indication(
        self,
        sample_patient_examination: Tuple[PatientExamination, PatientInterface],
        indication_name_screening_colonoscopy: str,
    ):
        patient_examination, patient_interface = sample_patient_examination

        examination_uuid = patient_examination.uuid

        patient_interface.add_indication_to_examination(
            examination_uuid=examination_uuid,
            indication_name=indication_name_screening_colonoscopy,
        )

        examination = patient_interface.get_patient_examination_by_uuid(
            examination_uuid
        )
        indications = examination.patient_indications
        indication_names = [indication.indication_name for indication in indications]

        assert indication_name_screening_colonoscopy in indication_names

    def test_patient_interface_add_indication_to_examination_raises(
        self,
        sample_patient_examination: Tuple[PatientExamination, PatientInterface],
        examination_name_colonoscopy: str,
        # indication_name_screening_colonoscopy: str,
    ):
        patient_examination, sample_patient_interface = sample_patient_examination
        assert patient_examination.examination_name == examination_name_colonoscopy

        non_existent = "Nonexistent"

        try:
            sample_patient_interface.add_indication_to_examination(
                examination_uuid=patient_examination.uuid,
                indication_name=non_existent,
            )
        except ValueError as e:
            assert (
                str(e)
                == f"Indication '{non_existent}' does not exist in the knowledge base."
            )
