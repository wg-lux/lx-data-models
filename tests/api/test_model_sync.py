import pytest

from lx_dtypes.contrib.lx_django.models import Patient as DjangoPatientModel
from lx_dtypes.models.patient.patient import Patient


@pytest.mark.django_db
class TestModelSync:
    def test_patient_sync(self, sample_patient: Patient) -> None:
        # Create a Django model instance from the sample_patient
        ddict = sample_patient.to_ddict()
        _django_patient = DjangoPatientModel.objects.create(**ddict)
        # Retrieve the Django model instance
        uuid = ddict.get("uuid")
        assert uuid is not None
        retrieved_patient = DjangoPatientModel.objects.get(uuid=uuid)
        assert str(retrieved_patient.uuid) == sample_patient.uuid
        patient_dict = retrieved_patient.to_ddict()
        # Convert the Django model instance back to a Pydantic model
        converted_patient = Patient.model_validate(patient_dict)
        assert converted_patient.to_ddict() == sample_patient.to_ddict()
