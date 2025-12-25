from typing import Tuple

from pytest import fixture

from lx_dtypes.lx_django.models import (
    Patient as DjangoPatientModel,
)
from lx_dtypes.lx_django.models.ledger.center import (
    Center as DjangoCenterModel,
)
from lx_dtypes.models.base_models.person import Person
from lx_dtypes.models.ledger.center import Center
from lx_dtypes.models.ledger.patient import (
    Patient,
    PatientDataDict,
    PatientDataShallowDict,
)


@fixture(scope="session")
def sample_patient(sample_person: Person, sample_center: Center) -> Patient:
    p = Patient.create_from_person(sample_person)
    p.center_name = sample_center.name
    return p


@fixture(scope="session")
def sample_patient_shallow(
    sample_person: Person, sample_center: Center
) -> PatientDataShallowDict:
    patient = Patient.create_from_person(sample_person)
    patient.center_name = sample_center.name
    return patient.to_ddict_shallow()


@fixture(scope="session")
def sample_patient_data_dict(sample_center: Center) -> PatientDataDict:
    ddict = PatientDataDict(
        uuid="123e4567-e89b-12d3-a456-426614174000",
        first_name="John",
        last_name="Doe",
        dob="1980-01-01",
        email="john.doe@example.com",
        gender="male",
        tags=[],
        center_name=sample_center.name,
    )
    return ddict


@fixture(scope="session")
def sample_patient_with_center(
    sample_center: Center, sample_patient: Patient
) -> Tuple[Patient, Center]:
    assert sample_patient.center_name == sample_center.name
    return sample_patient, sample_center


@fixture(scope="function")
def sample_django_patient_with_center(
    sample_patient_with_center: Tuple[Patient, Center],
    sample_django_center_with_examiners: DjangoCenterModel,
) -> "DjangoPatientModel":
    from lx_dtypes.lx_django.models.ledger.patient import (
        Patient as DjangoPatientModel,
    )

    sample_django_center = sample_django_center_with_examiners
    sample_django_center_name = sample_django_center.name

    sample_patient, sample_center = sample_patient_with_center

    assert sample_patient.center_name == sample_django_center_name, (
        f"Center names do not match between sample patient ({sample_patient.center_name}) and sample django center ({sample_django_center_name})."
    )

    ddict = sample_patient.to_ddict()
    django_patient = DjangoPatientModel.sync_from_ddict(ddict)

    django_patient.refresh_from_db()
    return django_patient
