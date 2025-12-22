from typing import Tuple

from pytest import fixture

from lx_dtypes.models.base_models.person import Person
from lx_dtypes.models.ledger.center import Center
from lx_dtypes.models.ledger.patient import (
    Patient,
    PatientDataDict,
    PatientDataShallowDict,
)


@fixture(scope="session")
def sample_patient(sample_person: Person) -> Patient:
    return Patient.create_from_person(sample_person)


@fixture(scope="session")
def sample_patient_shallow(sample_person: Person) -> PatientDataShallowDict:
    patient = Patient.create_from_person(sample_person)
    return patient.to_ddict_shallow()


@fixture(scope="session")
def sample_patient_data_dict() -> PatientDataDict:
    ddict = PatientDataDict(
        uuid="123e4567-e89b-12d3-a456-426614174000",
        first_name="John",
        last_name="Doe",
        dob="1980-01-01",
        email="john.doe@example.com",
        gender="male",
        tags=[],
        center_name="unknown",
    )
    return ddict


@fixture(scope="session")
def sample_patient_with_center(
    sample_center: Center, sample_patient: Patient
) -> Tuple[Patient, Center]:
    sample_patient.center_name = sample_center.name
    return sample_patient, sample_center
