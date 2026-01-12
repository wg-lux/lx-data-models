from typing import TypedDict, Union

from .DataDict import CenterDataDict
from .Django import CenterDjango
from .Pydantic import Center


class LCenterDjangoLookupType(TypedDict):
    Center: type[CenterDjango]


l_center_django_lookup = LCenterDjangoLookupType(
    Center=CenterDjango,
)


class LCenterLookupType(TypedDict):
    Center: type[Center]
    CenterDataDict: type[CenterDataDict]


l_center_lookup = LCenterLookupType(
    Center=Center,
    CenterDataDict=CenterDataDict,
)

l_center_models = Union[Center,]

l_center_ddicts = Union[CenterDataDict,]

l_center_django_models = Union[CenterDjango,]

__all__ = [
    "Center",
    "CenterDataDict",
    "l_center_django_models",
    "l_center_django_lookup",
    "LCenterDjangoLookupType",
    "l_center_lookup",
    "LCenterLookupType",
    "l_center_models",
    "l_center_ddicts",
]
