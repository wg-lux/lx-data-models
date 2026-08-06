from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypedDict, Union

from .Unit import Unit
from .UnitDataDict import UnitDataDict
from .UnitType import UnitType
from .UnitTypeDataDict import UnitTypeDataDict

if TYPE_CHECKING:
    from .UnitDjango import UnitDjango
    from .UnitTypeDjango import UnitTypeDjango


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

if TYPE_CHECKING:

    class KbUnitDjangoLookupType(TypedDict):
        Unit: type[UnitDjango]
        UnitType: type[UnitTypeDjango]

    kb_unit_django_lookup: KbUnitDjangoLookupType
    kb_unit_django_models = Union[UnitDjango, UnitTypeDjango]

__all__ = [
    "Unit",
    "UnitDataDict",
    "UnitType",
    "UnitTypeDataDict",
    "kb_unit_lookup",
    "KbUnitLookupType",
    "kb_unit_models",
    "kb_unit_ddicts",
    "kb_unit_django_models",
    "kb_unit_django_lookup",
    "KbUnitDjangoLookupType",
]


def __getattr__(name: str) -> Any:
    if name not in {
        "UnitDjango",
        "UnitTypeDjango",
        "KbUnitDjangoLookupType",
        "kb_unit_django_lookup",
        "kb_unit_django_models",
    }:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from .UnitDjango import UnitDjango
    from .UnitTypeDjango import UnitTypeDjango

    class KbUnitDjangoLookupType(TypedDict):
        Unit: type[UnitDjango]
        UnitType: type[UnitTypeDjango]

    exports = {
        "UnitDjango": UnitDjango,
        "UnitTypeDjango": UnitTypeDjango,
        "KbUnitDjangoLookupType": KbUnitDjangoLookupType,
        "kb_unit_django_lookup": KbUnitDjangoLookupType(
            Unit=UnitDjango,
            UnitType=UnitTypeDjango,
        ),
        "kb_unit_django_models": Union[UnitDjango, UnitTypeDjango],
    }
    globals().update(exports)
    return exports[name]
