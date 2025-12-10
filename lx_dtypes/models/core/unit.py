from pydantic import Field

from lx_dtypes.models.shallow.unit import (
    UnitShallow,
    UnitTypeShallow,
)
from lx_dtypes.utils.factories.field_defaults import list_of_unit_types_factory


class UnitType(UnitTypeShallow):
    pass


class Unit(UnitShallow):
    types: list[UnitType] = Field(default_factory=list_of_unit_types_factory)
