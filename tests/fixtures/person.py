from datetime import date

from pytest import fixture

from lx_dtypes.models.base_models.person import Person


@fixture(scope="session")
def sample_person_no_dob_no_gender() -> Person:
    return Person(first_name="John", last_name="Doe", dob=None, email=None)


@fixture(scope="session")
def sample_person() -> Person:
    dob = date(1985, 7, 20)
    return Person(first_name="Alice", last_name="Johnson", dob=dob, email=None, gender="female")
