from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict, Union

from .DataDict import CenterDataDict
from .Pydantic import Center

if TYPE_CHECKING:
    from .Django import CenterDjango

    class LCenterDjangoLookupType(TypedDict):
        Center: type[CenterDjango]

    l_center_django_lookup: LCenterDjangoLookupType
    type l_center_django_models = CenterDjango


class LCenterLookupType(TypedDict):
    Center: type[Center]
    CenterDataDict: type[CenterDataDict]


l_center_lookup = LCenterLookupType(
    Center=Center,
    CenterDataDict=CenterDataDict,
)

l_center_models = Union[Center,]

l_center_ddicts = Union[CenterDataDict,]


__all__ = [
    "Center",
    "CenterDataDict",
    "LCenterDjangoLookupType",
    "LCenterLookupType",
    "l_center_ddicts",
    "l_center_django_lookup",
    "l_center_django_models",
    "l_center_lookup",
    "l_center_models",
]


def __getattr__(name: str) -> object:
    if name not in {
        "CenterDjango",
        "LCenterDjangoLookupType",
        "l_center_django_lookup",
        "l_center_django_models",
    }:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from .Django import CenterDjango

    class LCenterDjangoLookupType(TypedDict):
        Center: type[CenterDjango]

    exports: dict[str, object] = {
        "CenterDjango": CenterDjango,
        "LCenterDjangoLookupType": LCenterDjangoLookupType,
        "l_center_django_lookup": LCenterDjangoLookupType(Center=CenterDjango),
        "l_center_django_models": CenterDjango,
    }
    globals().update(exports)
    return exports[name]
