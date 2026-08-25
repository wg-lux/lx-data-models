from typing import TypedDict, Union

from .DataDict import CaseDataDict
from .Pydantic import Case


class LCaseLookupType(TypedDict):
    Case: type[Case]
    CaseDataDict: type[CaseDataDict]


l_case_lookup = LCaseLookupType(Case=Case, CaseDataDict=CaseDataDict)
l_case_models = Union[Case,]
l_case_ddicts = Union[CaseDataDict,]

__all__ = [
    "Case",
    "CaseDataDict",
    "LCaseLookupType",
    "l_case_ddicts",
    "l_case_lookup",
    "l_case_models",
]
