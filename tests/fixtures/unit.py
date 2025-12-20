from pytest import fixture

from lx_dtypes.contrib.lx_django.models.core.unit import (
    Unit as DjangoUnitModel,
)
from lx_dtypes.contrib.lx_django.models.core.unit import (
    UnitType as DjangoUnitTypeModel,
)
from lx_dtypes.models.core.unit import Unit, UnitType


@fixture(scope="session")
def sample_unit_type() -> UnitType:
    return UnitType(
        name="Sample Unit Type",
        tags=[],
    )


@fixture(scope="function")
def sample_django_unit_type(sample_unit_type: UnitType) -> DjangoUnitTypeModel:
    ddict_unit_Type = sample_unit_type.to_ddict_shallow()
    django_unit_type = DjangoUnitTypeModel.sync_from_ddict_shallow(ddict_unit_Type)
    django_unit_type.refresh_from_db()
    return django_unit_type


@fixture(scope="session")
def sample_unit(sample_unit_type: UnitType) -> Unit:
    return Unit(
        name="Sample Unit",
        description="A sample measurement unit.",
        abbreviation="SU",
        type_names=[sample_unit_type.name],
        tags=[],
        types=[sample_unit_type],
    )


@fixture(scope="function")
def sample_django_unit(
    sample_unit: Unit, sample_django_unit_type: DjangoUnitTypeModel
) -> DjangoUnitModel:
    ddict_unit = sample_unit.to_ddict_shallow()
    django_unit = DjangoUnitModel.sync_from_ddict_shallow(ddict_unit)
    django_unit.refresh_from_db()
    return django_unit
