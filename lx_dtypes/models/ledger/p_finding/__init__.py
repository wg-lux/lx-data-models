from typing import TypedDict, Union

from .DataDict import PFindingDataDict
from .Django import PFindingDjango
from .Pydantic import PFinding


class LPFindingDjangoLookupType(TypedDict):
    PFinding: type[PFindingDjango]


l_p_finding_django_lookup = LPFindingDjangoLookupType(
    PFinding=PFindingDjango,
)


class LPFindingLookupType(TypedDict):
    PFinding: type[PFinding]
    PFindingDataDict: type[PFindingDataDict]


l_p_finding_lookup = LPFindingLookupType(
    PFinding=PFinding,
    PFindingDataDict=PFindingDataDict,
)
l_p_finding_models = Union[PFinding,]
l_p_finding_ddicts = Union[PFindingDataDict,]
l_p_finding_django_models = Union[PFindingDjango,]

__all__ = [
    "PFinding",
    "PFindingDataDict",
    "l_p_finding_django_models",
    "l_p_finding_django_lookup",
    "LPFindingDjangoLookupType",
    "l_p_finding_lookup",
    "LPFindingLookupType",
    "l_p_finding_models",
    "l_p_finding_ddicts",
]
