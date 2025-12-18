from pytest import fixture

from lx_dtypes.models.core.unit import Unit, UnitType


@fixture
def sample_unit_type() -> UnitType:
    return UnitType(
        name="Sample Unit Type",
        tags=[],
    )


@fixture
def sample_unit(sample_unit_type: UnitType) -> Unit:
    return Unit(
        name="Sample Unit",
        description="A sample measurement unit.",
        abbreviation="SU",
        type_names=[sample_unit_type.name],
        tags=[],
        types=[sample_unit_type],
    )
