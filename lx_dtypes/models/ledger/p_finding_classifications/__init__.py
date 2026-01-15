from typing import TypedDict, Union

from .DataDict import PFindingClassificationsDataDict
from .Django import PFindingClassificationsDjango
from .Pydantic import PFindingClassifications


class LPFindingClassificationsDjangoLookupType(TypedDict):
    PFindingClassifications: type[PFindingClassificationsDjango]


l_p_finding_classifications_django_lookup = LPFindingClassificationsDjangoLookupType(
    PFindingClassifications=PFindingClassificationsDjango,
)


class LPFindingClassificationsLookupType(TypedDict):
    PFindingClassifications: type[PFindingClassifications]
    PFindingClassificationsDataDict: type[PFindingClassificationsDataDict]


l_p_finding_classifications_lookup = LPFindingClassificationsLookupType(
    PFindingClassifications=PFindingClassifications,
    PFindingClassificationsDataDict=PFindingClassificationsDataDict,
)
l_p_finding_classifications_models = Union[PFindingClassifications,]
l_p_finding_classifications_ddicts = Union[PFindingClassificationsDataDict,]
l_p_finding_classifications_django_models = Union[PFindingClassificationsDjango,]
__all__ = [
    "PFindingClassifications",
    "PFindingClassificationsDataDict",
    "l_p_finding_classifications_django_models",
    "l_p_finding_classifications_django_lookup",
    "LPFindingClassificationsDjangoLookupType",
    "l_p_finding_classifications_lookup",
    "LPFindingClassificationsLookupType",
    "l_p_finding_classifications_models",
    "l_p_finding_classifications_ddicts",
]
