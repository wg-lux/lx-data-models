import pytest

from ..Unit import Unit
from ..UnitType import UnitType


@pytest.fixture(scope="session")
def unit_type_fixture() -> UnitType:
    return UnitType(
        name="sample_unit_type",
    )


@pytest.fixture(scope="session")
def unit_fixture(unit_type_fixture: UnitType) -> Unit:
    return Unit(
        name="sample_unit",
        unit_types=[unit_type_fixture.name, "test_unit_type2"],
    )
