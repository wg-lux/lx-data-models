from pytest import fixture

from lx_dtypes.models.base_models.person import Person
from lx_dtypes.models.examiner.examiner import (
    Examiner,
)


@fixture(scope="session")
def sample_examiner(sample_person: Person) -> Examiner:
    return Examiner.create_from_person(sample_person)
