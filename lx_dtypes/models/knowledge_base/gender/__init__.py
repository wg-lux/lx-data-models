from typing import TypedDict, Union

from .Gender import Gender
from .GenderDataDict import GenderDataDict


class KbGenderLookupType(TypedDict):
    Gender: type[Gender]
    GenderDataDict: type[GenderDataDict]


kb_gender_lookup = KbGenderLookupType(
    Gender=Gender,
    GenderDataDict=GenderDataDict,
)

kb_gender_models = Union[Gender]

kb_gender_ddicts = Union[GenderDataDict]

__all__ = [
    "Gender",
    "GenderDataDict",
    "kb_gender_lookup",
    "KbGenderLookupType",
    "kb_gender_models",
    "kb_gender_ddicts",
]
