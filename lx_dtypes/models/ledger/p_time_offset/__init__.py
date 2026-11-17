"""Ledger observation contracts with lazy Django adapters."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict, Union

from .DataDict import PTimeOffsetDataDict
from .Pydantic import PTimeOffset


class LPTimeOffsetLookupType(TypedDict):
    PTimeOffset: type[PTimeOffset]
    PTimeOffsetDataDict: type[PTimeOffsetDataDict]


l_p_time_offset_lookup = LPTimeOffsetLookupType(
    PTimeOffset=PTimeOffset,
    PTimeOffsetDataDict=PTimeOffsetDataDict,
)
l_p_time_offset_models = Union[PTimeOffset]
l_p_time_offset_ddicts = Union[PTimeOffsetDataDict]

if TYPE_CHECKING:
    from .Django import PTimeOffsetDjango

    l_p_time_offset_django_lookup: LPTimeOffsetDjangoLookupType
    type l_p_time_offset_django_models = PTimeOffsetDjango


class LPTimeOffsetDjangoLookupType(TypedDict):
    PTimeOffset: type[PTimeOffsetDjango]


__all__ = [
    "LPTimeOffsetDjangoLookupType",
    "LPTimeOffsetLookupType",
    "PTimeOffset",
    "PTimeOffsetDataDict",
    "l_p_time_offset_ddicts",
    "l_p_time_offset_django_lookup",
    "l_p_time_offset_django_models",
    "l_p_time_offset_lookup",
    "l_p_time_offset_models",
]


def __getattr__(name: str) -> object:
    if name not in {
        "l_p_time_offset_django_models",
        "l_p_time_offset_django_lookup",
        "PTimeOffsetDjango",
    }:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from .Django import PTimeOffsetDjango

    exports: dict[str, object] = {
        "PTimeOffsetDjango": PTimeOffsetDjango,
        "l_p_time_offset_django_lookup": LPTimeOffsetDjangoLookupType(
            PTimeOffset=PTimeOffsetDjango
        ),
        "l_p_time_offset_django_models": PTimeOffsetDjango,
    }
    globals().update(exports)
    return exports[name]
