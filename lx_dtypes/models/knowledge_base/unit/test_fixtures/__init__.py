import pytest

from ..Unit import Unit
from ..UnitDjango import UnitDjango
from ..UnitType import UnitType
from ..UnitTypeDjango import UnitTypeDjango


@pytest.fixture(scope="session")
def unit_type_fixture() -> UnitType:
    """
    Create a UnitType preconfigured with the name "sample_unit_type" for tests.

    Returns:
        UnitType: A UnitType instance whose name is "sample_unit_type".
    """
    return UnitType(
        name="sample_unit_type",
    )


@pytest.fixture(scope="session")
def unit_fixture(unit_type_fixture: UnitType) -> Unit:
    """
    Create a sample Unit with its unit_types set from the provided UnitType fixture.

    Parameters:
        unit_type_fixture (UnitType): Source UnitType whose `name` will be included in the created Unit's `unit_types` list.

    Returns:
        unit (Unit): A Unit named "sample_unit" whose `unit_types` contains the provided UnitType's name.
    """
    return Unit(
        name="sample_unit",
        unit_types=[unit_type_fixture.name],
    )


@pytest.fixture()
def django_unit_type_fixture(
    unit_type_fixture: UnitType,
) -> "UnitTypeDjango":
    """
    Create a Django UnitType model instance by syncing from the provided UnitType's ddict and refreshing it from the database.

    Parameters:
        unit_type_fixture (UnitType): Source UnitType instance whose `ddict` will be used to create the Django model.

    Returns:
        UnitTypeDjango: The created Django UnitType instance after calling `refresh_from_db()`.
    """
    from lx_dtypes.models.knowledge_base.unit.UnitTypeDjango import (
        UnitTypeDjango,
    )

    unit_type_django = UnitTypeDjango.sync_from_ddict(unit_type_fixture.ddict)
    unit_type_django.refresh_from_db()

    return unit_type_django


@pytest.fixture()
def django_unit_fixture(
    unit_fixture: Unit,
    django_unit_type_fixture: UnitTypeDjango,
) -> "UnitDjango":
    """
    Create a UnitDjango model instance from the provided Unit fixture's ddict and refresh it from the database.

    Parameters:
        unit_fixture (Unit): Unit instance whose `ddict` is used to synchronize and create the Django model.
        django_unit_type_fixture (UnitTypeDjango): Django UnitType fixture used to ensure the related unit type exists in the database.

    Returns:
        UnitDjango: The synchronized Django model instance refreshed from the database.
    """
    from lx_dtypes.models.knowledge_base.unit.UnitDjango import (
        UnitDjango,
    )

    unit_django = UnitDjango.sync_from_ddict(unit_fixture.ddict)
    unit_django.refresh_from_db()

    return unit_django
