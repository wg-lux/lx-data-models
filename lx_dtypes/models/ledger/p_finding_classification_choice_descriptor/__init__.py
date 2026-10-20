from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict, Union

from .DataDict import PFindingClassificationChoiceDescriptorDataDict
from .Pydantic import PFindingClassificationChoiceDescriptor

if TYPE_CHECKING:
    from .Django import PFindingClassificationChoiceDescriptorDjango

    l_p_finding_classification_choice_descriptor_django_lookup: (
        LPFindingClassificationChoiceDescriptorDjangoLookupType
    )
    type l_p_finding_classification_choice_descriptor_django_models = (
        PFindingClassificationChoiceDescriptorDjango
    )


class LPFindingClassificationChoiceDescriptorDjangoLookupType(TypedDict):
    PFindingClassificationChoiceDescriptor: type[
        PFindingClassificationChoiceDescriptorDjango
    ]


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

__all__ = [
    "LPFindingClassificationChoiceDescriptorDjangoLookupType",
    "LPFindingClassificationChoiceDescriptorLookupType",
    "PFindingClassificationChoiceDescriptor",
    "PFindingClassificationChoiceDescriptorDataDict",
    "l_p_finding_classification_choice_descriptor_ddicts",
    "l_p_finding_classification_choice_descriptor_django_lookup",
    "l_p_finding_classification_choice_descriptor_django_models",
    "l_p_finding_classification_choice_descriptor_lookup",
    "l_p_finding_classification_choice_descriptor_models",
]


def __getattr__(name: str) -> object:
    if name not in {
        "PFindingClassificationChoiceDescriptorDjango",
        "l_p_finding_classification_choice_descriptor_django_lookup",
        "l_p_finding_classification_choice_descriptor_django_models",
    }:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from .Django import PFindingClassificationChoiceDescriptorDjango

    exports: dict[str, object] = {
        "PFindingClassificationChoiceDescriptorDjango": PFindingClassificationChoiceDescriptorDjango,
        "l_p_finding_classification_choice_descriptor_django_lookup": LPFindingClassificationChoiceDescriptorDjangoLookupType(
            PFindingClassificationChoiceDescriptor=PFindingClassificationChoiceDescriptorDjango
        ),
        "l_p_finding_classification_choice_descriptor_django_models": PFindingClassificationChoiceDescriptorDjango,
    }
    globals().update(exports)
    return exports[name]
