from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict, Union

from .DataDict import PIndicationDataDict
from .Pydantic import PIndication

if TYPE_CHECKING:
    from .Django import PIndicationDjango

    l_p_indication_django_lookup: LPIndicationDjangoLookupType
    type l_p_indication_django_models = PIndicationDjango


class LPIndicationDjangoLookupType(TypedDict):
    PIndication: type[PIndicationDjango]


class LPIndicationLookupType(TypedDict):
    PIndication: type[PIndication]
    PIndicationDataDict: type[PIndicationDataDict]


l_p_indication_lookup = LPIndicationLookupType(
    PIndication=PIndication,
    PIndicationDataDict=PIndicationDataDict,
)
l_p_indication_models = Union[PIndication,]
l_p_indication_ddicts = Union[PIndicationDataDict,]

__all__ = [
    "LPIndicationDjangoLookupType",
    "LPIndicationLookupType",
    "PIndication",
    "PIndicationDataDict",
    "l_p_indication_ddicts",
    "l_p_indication_django_lookup",
    "l_p_indication_django_models",
    "l_p_indication_lookup",
    "l_p_indication_models",
]


def __getattr__(name: str) -> object:
    if name not in {
        "PIndicationDjango",
        "l_p_indication_django_lookup",
        "l_p_indication_django_models",
    }:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from .Django import PIndicationDjango

    exports: dict[str, object] = {
        "PIndicationDjango": PIndicationDjango,
        "l_p_indication_django_lookup": LPIndicationDjangoLookupType(
            PIndication=PIndicationDjango
        ),
        "l_p_indication_django_models": PIndicationDjango,
    }
    globals().update(exports)
    return exports[name]
