from typing import TypedDict, Union

from .DataDict import PIndicationDataDict
from .Django import PIndicationDjango
from .Pydantic import PIndication


class LPIndicationDjangoLookupType(TypedDict):
    PIndication: type[PIndicationDjango]


l_p_indication_django_lookup = LPIndicationDjangoLookupType(
    PIndication=PIndicationDjango,
)


class LPIndicationLookupType(TypedDict):
    PIndication: type[PIndication]
    PIndicationDataDict: type[PIndicationDataDict]


l_p_indication_lookup = LPIndicationLookupType(
    PIndication=PIndication,
    PIndicationDataDict=PIndicationDataDict,
)
l_p_indication_models = Union[PIndication,]
l_p_indication_ddicts = Union[PIndicationDataDict,]
l_p_indication_django_models = Union[PIndicationDjango,]

__all__ = [
    "PIndication",
    "PIndicationDataDict",
    "l_p_indication_django_models",
    "l_p_indication_django_lookup",
    "LPIndicationDjangoLookupType",
    "l_p_indication_lookup",
    "LPIndicationLookupType",
    "l_p_indication_models",
    "l_p_indication_ddicts",
]
