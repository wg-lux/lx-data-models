from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict, Union

from .DataDict import PFindingClassificationChoiceDataDict
from .Pydantic import PFindingClassificationChoice

if TYPE_CHECKING:
    from .Django import PFindingClassificationChoiceDjango

    l_p_finding_classification_choice_django_lookup: (
        LPFindingClassificationChoiceDjangoLookupType
    )
    type l_p_finding_classification_choice_django_models = (
        PFindingClassificationChoiceDjango
    )


class LPFindingClassificationChoiceDjangoLookupType(TypedDict):
    PFindingClassificationChoice: type[PFindingClassificationChoiceDjango]


class LPFindingClassificationChoiceLookupType(TypedDict):
    PFindingClassificationChoice: type[PFindingClassificationChoice]
    PFindingClassificationChoiceDataDict: type[PFindingClassificationChoiceDataDict]


l_p_finding_classification_choice_lookup = LPFindingClassificationChoiceLookupType(
    PFindingClassificationChoice=PFindingClassificationChoice,
    PFindingClassificationChoiceDataDict=PFindingClassificationChoiceDataDict,
)

l_p_finding_classification_choice_models = Union[PFindingClassificationChoice,]
l_p_finding_classification_choice_ddicts = Union[PFindingClassificationChoiceDataDict,]

__all__ = [
    "LPFindingClassificationChoiceDjangoLookupType",
    "LPFindingClassificationChoiceLookupType",
    "PFindingClassificationChoice",
    "PFindingClassificationChoiceDataDict",
    "l_p_finding_classification_choice_ddicts",
    "l_p_finding_classification_choice_django_lookup",
    "l_p_finding_classification_choice_django_models",
    "l_p_finding_classification_choice_lookup",
    "l_p_finding_classification_choice_models",
]


def __getattr__(name: str) -> object:
    if name not in {
        "PFindingClassificationChoiceDjango",
        "l_p_finding_classification_choice_django_lookup",
        "l_p_finding_classification_choice_django_models",
    }:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from .Django import PFindingClassificationChoiceDjango

    exports: dict[str, object] = {
        "PFindingClassificationChoiceDjango": PFindingClassificationChoiceDjango,
        "l_p_finding_classification_choice_django_lookup": LPFindingClassificationChoiceDjangoLookupType(
            PFindingClassificationChoice=PFindingClassificationChoiceDjango
        ),
        "l_p_finding_classification_choice_django_models": PFindingClassificationChoiceDjango,
    }
    globals().update(exports)
    return exports[name]
