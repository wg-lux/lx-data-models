"""Ledger observation contracts with lazy Django adapters."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict, Union

from .DataDict import PElectricalApplicationDataDict, PElectricalCurveComparisonDataDict
from .Pydantic import PElectricalApplication, PElectricalCurveComparison


class LPElectricalApplicationLookupType(TypedDict):
    PElectricalApplication: type[PElectricalApplication]
    PElectricalCurveComparison: type[PElectricalCurveComparison]
    PElectricalApplicationDataDict: type[PElectricalApplicationDataDict]
    PElectricalCurveComparisonDataDict: type[PElectricalCurveComparisonDataDict]


l_p_electrical_application_lookup = LPElectricalApplicationLookupType(
    PElectricalApplication=PElectricalApplication,
    PElectricalCurveComparison=PElectricalCurveComparison,
    PElectricalApplicationDataDict=PElectricalApplicationDataDict,
    PElectricalCurveComparisonDataDict=PElectricalCurveComparisonDataDict,
)
l_p_electrical_application_models = Union[
    PElectricalApplication, PElectricalCurveComparison
]
l_p_electrical_application_ddicts = Union[
    PElectricalApplicationDataDict, PElectricalCurveComparisonDataDict
]

if TYPE_CHECKING:
    from .Django import PElectricalApplicationDjango, PElectricalCurveComparisonDjango

    l_p_electrical_application_django_lookup: LPElectricalApplicationDjangoLookupType
    type l_p_electrical_application_django_models = (
        PElectricalApplicationDjango | PElectricalCurveComparisonDjango
    )


class LPElectricalApplicationDjangoLookupType(TypedDict):
    PElectricalApplication: type[PElectricalApplicationDjango]
    PElectricalCurveComparison: type[PElectricalCurveComparisonDjango]


__all__ = [
    "LPElectricalApplicationDjangoLookupType",
    "LPElectricalApplicationLookupType",
    "PElectricalApplication",
    "PElectricalApplicationDataDict",
    "PElectricalCurveComparison",
    "PElectricalCurveComparisonDataDict",
    "l_p_electrical_application_ddicts",
    "l_p_electrical_application_django_lookup",
    "l_p_electrical_application_django_models",
    "l_p_electrical_application_lookup",
    "l_p_electrical_application_models",
]


def __getattr__(name: str) -> object:
    if name not in {
        "l_p_electrical_application_django_lookup",
        "PElectricalCurveComparisonDjango",
        "l_p_electrical_application_django_models",
        "PElectricalApplicationDjango",
    }:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from .Django import PElectricalApplicationDjango, PElectricalCurveComparisonDjango

    exports: dict[str, object] = {
        "PElectricalApplicationDjango": PElectricalApplicationDjango,
        "PElectricalCurveComparisonDjango": PElectricalCurveComparisonDjango,
        "l_p_electrical_application_django_lookup": LPElectricalApplicationDjangoLookupType(
            PElectricalApplication=PElectricalApplicationDjango,
            PElectricalCurveComparison=PElectricalCurveComparisonDjango,
        ),
        "l_p_electrical_application_django_models": PElectricalApplicationDjango
        | PElectricalCurveComparisonDjango,
    }
    globals().update(exports)
    return exports[name]
