import pytest

from ..Examination import Examination
from ..ExaminationType import ExaminationType


@pytest.fixture(scope="session")
def examination_type_fixture() -> ExaminationType:
    return ExaminationType(
        name="sample_examination_type",
        description="This is a sample examination type for testing purposes.",
        tags=["tagA", "tagB"],
    )


@pytest.fixture(scope="session")
def examination_fixture(examination_type_fixture: ExaminationType) -> Examination:
    return Examination(
        name="sample_examination",
        description="This is a sample examination for testing purposes.",
        tags=["tag1", "tag2"],
        examination_types=[examination_type_fixture.name],
    )
