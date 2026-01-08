from typing import TypedDict, Union

from .Unit import Unit
from .UnitDataDict import UnitDataDict
from .UnitType import UnitType
from .UnitTypeDataDict import UnitTypeDataDict


class KbUnitLookupType(TypedDict):
    Unit: type[Unit]
    UnitDataDict: type[UnitDataDict]
    UnitType: type[UnitType]
    UnitTypeDataDict: type[UnitTypeDataDict]


kb_unit_lookup = KbUnitLookupType(
    Unit=Unit,
    UnitDataDict=UnitDataDict,
    UnitType=UnitType,
    UnitTypeDataDict=UnitTypeDataDict,
)

kb_unit_models = Union[
    Unit,
    UnitType,
]

kb_unit_ddicts = Union[
    UnitDataDict,
    UnitTypeDataDict,
]

__all__ = [
    "Unit",
    "UnitDataDict",
    "UnitType",
    "UnitTypeDataDict",
    "kb_unit_lookup",
    "KbUnitLookupType",
    "kb_unit_models",
    "kb_unit_ddicts",
]
