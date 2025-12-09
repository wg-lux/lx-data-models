from lx_dtypes.models.base_models.person import Person
from lx_dtypes.models.patient.patient import Patient


class TestPatientModel:
    def test_create_from_person(self, sample_patient: Patient, sample_person: Person):
        assert sample_patient.first_name == sample_person.first_name
        assert sample_patient.last_name == sample_person.last_name
        assert sample_patient.dob == sample_person.dob
        assert sample_patient.email == sample_person.email
        assert sample_patient.gender == sample_person.gender
        assert sample_patient.uuid == sample_person.uuid
