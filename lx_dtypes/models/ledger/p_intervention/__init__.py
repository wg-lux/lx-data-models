from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict, Union

from .DataDict import (
    PFindingInterventionDataDict,
)
from .Pydantic import (
    PFindingIntervention,
)

if TYPE_CHECKING:
    from .Django import PFindingInterventionDjango

    l_p_finding_intervention_django_lookup: LPFindingInterventionDjangoLookupType
    type l_p_finding_intervention_django_models = PFindingInterventionDjango


class LPFindingInterventionDjangoLookupType(TypedDict):
    PFindingIntervention: type[PFindingInterventionDjango]


class LPFindingInterventionLookupType(TypedDict):
    PFindingIntervention: type[PFindingIntervention]
    PFindingInterventionDataDict: type[PFindingInterventionDataDict]


l_p_finding_intervention_lookup = LPFindingInterventionLookupType(
    PFindingIntervention=PFindingIntervention,
    PFindingInterventionDataDict=PFindingInterventionDataDict,
)

l_p_finding_intervention_models = Union[PFindingIntervention,]
l_p_finding_intervention_ddicts = Union[PFindingInterventionDataDict,]

__all__ = [
    "LPFindingInterventionDjangoLookupType",
    "LPFindingInterventionLookupType",
    "PFindingIntervention",
    "PFindingInterventionDataDict",
    "l_p_finding_intervention_ddicts",
    "l_p_finding_intervention_django_lookup",
    "l_p_finding_intervention_django_models",
    "l_p_finding_intervention_lookup",
    "l_p_finding_intervention_models",
]


def __getattr__(name: str) -> object:
    if name not in {
        "PFindingInterventionDjango",
        "l_p_finding_intervention_django_lookup",
        "l_p_finding_intervention_django_models",
    }:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from .Django import PFindingInterventionDjango

    exports: dict[str, object] = {
        "PFindingInterventionDjango": PFindingInterventionDjango,
        "l_p_finding_intervention_django_lookup": LPFindingInterventionDjangoLookupType(
            PFindingIntervention=PFindingInterventionDjango
        ),
        "l_p_finding_intervention_django_models": PFindingInterventionDjango,
    }
    globals().update(exports)
    return exports[name]
