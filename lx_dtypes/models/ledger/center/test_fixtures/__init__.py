import pytest

from lx_dtypes.models.ledger.examiner.Django import ExaminerDjango

from ..Django import (
    CenterDjango,
)
from ..Pydantic import Center


@pytest.fixture(scope="session")
def center_fixture() -> Center:
    """
    Create a Center instance pre-populated with sample data for tests.

    Returns:
        Center: A Center named "sample_center" with tags ["tag1", "tag2"].
    """
    return Center(
        name="sample_center",
        tags=["tag1", "tag2"],
    )


@pytest.fixture()
def django_center_fixture(
    center_fixture: Center,
) -> "CenterDjango":
    """
    Create a CenterDjango instance from a Center pydantic model and ensure the instance is current with the database.

    Parameters:
        center_fixture (Center): The Center pydantic model whose data will be used to create or update the Django model.

    Returns:
        CenterDjango: The CenterDjango instance created/updated from the provided Center and refreshed from the database.
    """
    center_django = CenterDjango.sync_from_ddict(center_fixture.ddict)
    center_django.refresh_from_db()

    return center_django


@pytest.fixture()
def django_populated_center_fixture(
    django_center_fixture: "CenterDjango",
    django_examiner_fixture: ExaminerDjango,
) -> "CenterDjango":
    """
    Ensure the given CenterDjango has the provided ExaminerDjango linked and return the refreshed center.

    Parameters:
        django_center_fixture (CenterDjango): CenterDjango instance to refresh and validate.
        django_examiner_fixture (ExaminerDjango): ExaminerDjango expected to be related to the center.

    Returns:
        CenterDjango: The refreshed CenterDjango instance.

    Raises:
        ValueError: If the examiner is not linked to the center.
    """
    django_center_fixture.refresh_from_db()
    # assert that examiner is linked
    all_examiners = django_center_fixture.examiners.all()

    if django_examiner_fixture not in all_examiners:
        raise ValueError(
            "The django_examiner_fixture is not linked to the django_center_fixture."
        )

    return django_center_fixture
