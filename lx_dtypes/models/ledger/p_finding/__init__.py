from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict, Union

from .DataDict import PFindingDataDict
from .Pydantic import PFinding

if TYPE_CHECKING:
    from .Django import PFindingDjango

    l_p_finding_django_lookup: LPFindingDjangoLookupType
    type l_p_finding_django_models = PFindingDjango


class LPFindingDjangoLookupType(TypedDict):
    PFinding: type[PFindingDjango]


class LPFindingLookupType(TypedDict):
    PFinding: type[PFinding]
    PFindingDataDict: type[PFindingDataDict]


l_p_finding_lookup = LPFindingLookupType(
    PFinding=PFinding,
    PFindingDataDict=PFindingDataDict,
)
l_p_finding_models = Union[PFinding,]
l_p_finding_ddicts = Union[PFindingDataDict,]

__all__ = [
    "LPFindingDjangoLookupType",
    "LPFindingLookupType",
    "PFinding",
    "PFindingDataDict",
    "l_p_finding_ddicts",
    "l_p_finding_django_lookup",
    "l_p_finding_django_models",
    "l_p_finding_lookup",
    "l_p_finding_models",
]


def __getattr__(name: str) -> object:
    if name not in {
        "PFindingDjango",
        "l_p_finding_django_lookup",
        "l_p_finding_django_models",
    }:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from .Django import PFindingDjango

    exports: dict[str, object] = {
        "PFindingDjango": PFindingDjango,
        "l_p_finding_django_lookup": LPFindingDjangoLookupType(PFinding=PFindingDjango),
        "l_p_finding_django_models": PFindingDjango,
    }
    globals().update(exports)
    return exports[name]
