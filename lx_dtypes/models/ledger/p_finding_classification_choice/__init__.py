from typing import TypedDict, Union

from .DataDict import PFindingClassificationChoiceDataDict
from .Django import PFindingClassificationChoiceDjango
from .Pydantic import PFindingClassificationChoice


class LPFindingClassificationChoiceDjangoLookupType(TypedDict):
    PFindingClassificationChoice: type[PFindingClassificationChoiceDjango]


l_p_finding_classification_choice_django_lookup = (
    LPFindingClassificationChoiceDjangoLookupType(
        PFindingClassificationChoice=PFindingClassificationChoiceDjango,
    )
)


class LPFindingClassificationChoiceLookupType(TypedDict):
    PFindingClassificationChoice: type[PFindingClassificationChoice]
    PFindingClassificationChoiceDataDict: type[PFindingClassificationChoiceDataDict]


l_p_finding_classification_choice_lookup = LPFindingClassificationChoiceLookupType(
    PFindingClassificationChoice=PFindingClassificationChoice,
    PFindingClassificationChoiceDataDict=PFindingClassificationChoiceDataDict,
)

l_p_finding_classification_choice_models = Union[PFindingClassificationChoice,]
l_p_finding_classification_choice_ddicts = Union[PFindingClassificationChoiceDataDict,]
l_p_finding_classification_choice_django_models = Union[
    PFindingClassificationChoiceDjango,
]

__all__ = [
    "PFindingClassificationChoice",
    "PFindingClassificationChoiceDataDict",
    "l_p_finding_classification_choice_django_models",
    "l_p_finding_classification_choice_django_lookup",
    "LPFindingClassificationChoiceDjangoLookupType",
    "l_p_finding_classification_choice_lookup",
    "LPFindingClassificationChoiceLookupType",
    "l_p_finding_classification_choice_models",
    "l_p_finding_classification_choice_ddicts",
]
