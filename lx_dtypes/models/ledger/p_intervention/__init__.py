from typing import TypedDict, Union

from .DataDict import (
    PFindingInterventionDataDict,
)
from .Django import (
    PFindingInterventionDjango,
)
from .Pydantic import (
    PFindingIntervention,
)


class LPFindingInterventionDjangoLookupType(TypedDict):
    PFindingIntervention: type[PFindingInterventionDjango]


l_p_finding_intervention_django_lookup = LPFindingInterventionDjangoLookupType(
    PFindingIntervention=PFindingInterventionDjango,
)


class LPFindingInterventionLookupType(TypedDict):
    PFindingIntervention: type[PFindingIntervention]
    PFindingInterventionDataDict: type[PFindingInterventionDataDict]


l_p_finding_intervention_lookup = LPFindingInterventionLookupType(
    PFindingIntervention=PFindingIntervention,
    PFindingInterventionDataDict=PFindingInterventionDataDict,
)

l_p_finding_intervention_models = Union[PFindingIntervention,]
l_p_finding_intervention_ddicts = Union[PFindingInterventionDataDict,]
l_p_finding_intervention_django_models = Union[PFindingInterventionDjango,]

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
