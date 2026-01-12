import pytest

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
