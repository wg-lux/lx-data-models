from pytest import fixture

from lx_dtypes.models.patient.patient import Patient
from lx_dtypes.models.base_models.person import Person


@fixture(scope="session")
def sample_patient(sample_person: Person) -> Patient:
    return Patient.create_from_person(sample_person)
