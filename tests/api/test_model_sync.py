import pytest

from lx_dtypes.contrib.lx_django.models import Patient as DjangoPatientModel
from lx_dtypes.models.patient.patient import Patient


@pytest.mark.django_db
class TestModelSync:
    def test_patient_sync(self, sample_patient: Patient) -> None:
        ddict = sample_patient.to_ddict()
        _django_patient = DjangoPatientModel.objects.create(**ddict)
        uuid = ddict.get("uuid")
        assert uuid is not None
        retrieved_patient = DjangoPatientModel.objects.get(uuid=uuid)
        assert str(retrieved_patient.uuid) == sample_patient.uuid
        patient_dict = retrieved_patient.to_ddict()
        # Convert the Django model instance back to a Pydantic model
        converted_patient = Patient.model_validate(patient_dict)
        assert converted_patient.to_ddict() == sample_patient.to_ddict()

    # def test_examiner_sync(self, sample_examiner: Examiner) -> None:

    # def test_center_sync(self, sample_center: Center) -> None:

    # def test_examination_sync(self, sample_exam: Exam) -> None:

    # def test_finding_sync(self, sample_finding: Finding) -> None:

    # def test_classification_sync(self, sample_classification: Classification) -> None:

    # def test_classification_choice_sync(self, sample_classification_choice: ClassificationChoice) -> None:

    # def test_classification_choice_descriptor_sync(self, sample_classification_choice_descriptor: ClassificationChoiceDescriptor) -> None:

    # def test_citation_sync(self, sample_citation: Citation) -> None:

    # def test_indication_sync(self, sample_indication: Indication) -> None:

    # def test_intervention_sync(self, sample_intervention: Intervention) -> None:

    # def test_information_source_sync(self, sample_information_source: InformationSource) -> None:

    # def test_unit_sync(self, sample_unit: Unit) -> None:

    # def test_patient_examination_sync(self, sample_patient_examination: PatientExamination) -> None:

    #
