from typing import TypedDict, Union

from .DataDict import PFindingClassificationChoiceDescriptorDataDict
from .Django import PFindingClassificationChoiceDescriptorDjango
from .Pydantic import PFindingClassificationChoiceDescriptor


class LPFindingClassificationChoiceDescriptorDjangoLookupType(TypedDict):
    PFindingClassificationChoiceDescriptor: type[
        PFindingClassificationChoiceDescriptorDjango
    ]


l_p_finding_classification_choice_descriptor_django_lookup = LPFindingClassificationChoiceDescriptorDjangoLookupType(
    PFindingClassificationChoiceDescriptor=PFindingClassificationChoiceDescriptorDjango,
)


class LPFindingClassificationChoiceDescriptorLookupType(TypedDict):
    PFindingClassificationChoiceDescriptor: type[PFindingClassificationChoiceDescriptor]
    PFindingClassificationChoiceDescriptorDataDict: type[
        PFindingClassificationChoiceDescriptorDataDict
    ]


l_p_finding_classification_choice_descriptor_lookup = LPFindingClassificationChoiceDescriptorLookupType(
    PFindingClassificationChoiceDescriptor=PFindingClassificationChoiceDescriptor,
    PFindingClassificationChoiceDescriptorDataDict=PFindingClassificationChoiceDescriptorDataDict,
)

l_p_finding_classification_choice_descriptor_models = Union[
    PFindingClassificationChoiceDescriptor,
]
l_p_finding_classification_choice_descriptor_ddicts = Union[
    PFindingClassificationChoiceDescriptorDataDict,
]
l_p_finding_classification_choice_descriptor_django_models = Union[
    PFindingClassificationChoiceDescriptorDjango,
]

__all__ = [
    "PFindingClassificationChoiceDescriptor",
    "PFindingClassificationChoiceDescriptorDataDict",
    "l_p_finding_classification_choice_descriptor_django_models",
    "l_p_finding_classification_choice_descriptor_django_lookup",
    "LPFindingClassificationChoiceDescriptorDjangoLookupType",
    "l_p_finding_classification_choice_descriptor_lookup",
    "LPFindingClassificationChoiceDescriptorLookupType",
    "l_p_finding_classification_choice_descriptor_models",
    "l_p_finding_classification_choice_descriptor_ddicts",
]
