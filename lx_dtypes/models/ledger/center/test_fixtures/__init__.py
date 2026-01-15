import pytest

from lx_dtypes.models.ledger.examiner.Django import ExaminerDjango

from ..Django import (
    CenterDjango,
)
from ..Pydantic import Center


@pytest.fixture(scope="session")
def center_fixture() -> Center:
    return Center(
        name="sample_center",
        tags=["tag1", "tag2"],
    )


@pytest.fixture()
def django_center_fixture(
    center_fixture: Center,
) -> "CenterDjango":
    center_django = CenterDjango.sync_from_ddict(center_fixture.ddict)
    center_django.refresh_from_db()

    return center_django


@pytest.fixture()
def django_populated_center_fixture(
    django_center_fixture: "CenterDjango",
    django_examiner_fixture: ExaminerDjango,
) -> "CenterDjango":
    django_center_fixture.refresh_from_db()
    # assert that examiner is linked
    all_examiners = django_center_fixture.examiners.all()

    if django_examiner_fixture not in all_examiners:
        raise ValueError(
            "The django_examiner_fixture is not linked to the django_center_fixture."
        )

    return django_center_fixture
