import pytest

from ..Unit import Unit
from ..UnitDjango import UnitDjango
from ..UnitType import UnitType
from ..UnitTypeDjango import UnitTypeDjango


@pytest.fixture(scope="session")
def unit_type_fixture() -> UnitType:
    return UnitType(
        name="sample_unit_type",
    )


@pytest.fixture(scope="session")
def unit_fixture(unit_type_fixture: UnitType) -> Unit:
    return Unit(
        name="sample_unit",
        unit_types=[unit_type_fixture.name],
    )


@pytest.fixture()
def django_unit_type_fixture(
    unit_type_fixture: UnitType,
) -> "UnitTypeDjango":
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
    from lx_dtypes.models.knowledge_base.unit.UnitDjango import (
        UnitDjango,
    )

    unit_django = UnitDjango.sync_from_ddict(unit_fixture.ddict)
    unit_django.refresh_from_db()

    return unit_django
