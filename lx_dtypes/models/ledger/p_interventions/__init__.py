from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict, Union

from .DataDict import (
    PFindingInterventionsDataDict,
)
from .Pydantic import (
    PFindingInterventions,
)

if TYPE_CHECKING:
    from .Django import PFindingInterventionsDjango

    l_p_finding_interventions_django_lookup: LPFindingInterventionsDjangoLookupType
    type l_p_finding_interventions_django_models = PFindingInterventionsDjango


class LPFindingInterventionsDjangoLookupType(TypedDict):
    PFindingInterventions: type[PFindingInterventionsDjango]


class LPFindingInterventionsLookupType(TypedDict):
    PFindingInterventions: type[PFindingInterventions]
    PFindingInterventionsDataDict: type[PFindingInterventionsDataDict]


l_p_finding_interventions_lookup = LPFindingInterventionsLookupType(
    PFindingInterventions=PFindingInterventions,
    PFindingInterventionsDataDict=PFindingInterventionsDataDict,
)

l_p_finding_interventions_models = Union[PFindingInterventions,]
l_p_finding_interventions_ddicts = Union[PFindingInterventionsDataDict,]

__all__ = [
    "LPFindingInterventionsDjangoLookupType",
    "LPFindingInterventionsLookupType",
    "PFindingInterventions",
    "PFindingInterventionsDataDict",
    "l_p_finding_interventions_ddicts",
    "l_p_finding_interventions_django_lookup",
    "l_p_finding_interventions_django_models",
    "l_p_finding_interventions_lookup",
    "l_p_finding_interventions_models",
]


def __getattr__(name: str) -> object:
    if name not in {
        "PFindingInterventionsDjango",
        "l_p_finding_interventions_django_lookup",
        "l_p_finding_interventions_django_models",
    }:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from .Django import PFindingInterventionsDjango

    exports: dict[str, object] = {
        "PFindingInterventionsDjango": PFindingInterventionsDjango,
        "l_p_finding_interventions_django_lookup": LPFindingInterventionsDjangoLookupType(
            PFindingInterventions=PFindingInterventionsDjango
        ),
        "l_p_finding_interventions_django_models": PFindingInterventionsDjango,
    }
    globals().update(exports)
    return exports[name]
