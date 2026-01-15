from typing import TypedDict, Union

from .DataDict import (
    PFindingInterventionsDataDict,
)
from .Django import (
    PFindingInterventionsDjango,
)
from .Pydantic import (
    PFindingInterventions,
)


class LPFindingInterventionsDjangoLookupType(TypedDict):
    PFindingInterventions: type[PFindingInterventionsDjango]


l_p_finding_interventions_django_lookup = LPFindingInterventionsDjangoLookupType(
    PFindingInterventions=PFindingInterventionsDjango,
)


class LPFindingInterventionsLookupType(TypedDict):
    PFindingInterventions: type[PFindingInterventions]
    PFindingInterventionsDataDict: type[PFindingInterventionsDataDict]


l_p_finding_interventions_lookup = LPFindingInterventionsLookupType(
    PFindingInterventions=PFindingInterventions,
    PFindingInterventionsDataDict=PFindingInterventionsDataDict,
)

l_p_finding_interventions_models = Union[PFindingInterventions,]
l_p_finding_interventions_ddicts = Union[PFindingInterventionsDataDict,]
l_p_finding_interventions_django_models = Union[PFindingInterventionsDjango,]

__all__ = [
    "PFindingInterventions",
    "PFindingInterventionsDataDict",
    "l_p_finding_interventions_django_models",
    "l_p_finding_interventions_django_lookup",
    "LPFindingInterventionsDjangoLookupType",
    "l_p_finding_interventions_lookup",
    "LPFindingInterventionsLookupType",
    "l_p_finding_interventions_models",
    "l_p_finding_interventions_ddicts",
]
