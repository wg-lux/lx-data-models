from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypedDict, Union

from .ClassificationChoice import ClassificationChoice
from .ClassificationChoiceDataDict import ClassificationChoiceDataDict

if TYPE_CHECKING:
    from .ClassificationChoiceDjango import ClassificationChoiceDjango


class KbClassificationChoiceLookupType(TypedDict):
    ClassificationChoice: type[ClassificationChoice]
    ClassificationChoiceDataDict: type[ClassificationChoiceDataDict]


kb_classification_choice_lookup = KbClassificationChoiceLookupType(
    ClassificationChoice=ClassificationChoice,
    ClassificationChoiceDataDict=ClassificationChoiceDataDict,
)

kb_classification_choice_models = Union[ClassificationChoice,]

kb_classification_choice_ddicts = Union[ClassificationChoiceDataDict,]

if TYPE_CHECKING:

    class KbClassificationChoiceDjangoLookupType(TypedDict):
        ClassificationChoice: type[ClassificationChoiceDjango]

    kb_classification_choice_django_lookup: KbClassificationChoiceDjangoLookupType
    kb_classification_choice_django_models = Union[ClassificationChoiceDjango,]

__all__ = [
    "ClassificationChoice",
    "ClassificationChoiceDataDict",
    "kb_classification_choice_django_models",
    "kb_classification_choice_django_lookup",
    "KbClassificationChoiceDjangoLookupType",
    "kb_classification_choice_lookup",
    "KbClassificationChoiceLookupType",
    "kb_classification_choice_models",
    "kb_classification_choice_ddicts",
]


def __getattr__(name: str) -> Any:
    if name not in {
        "ClassificationChoiceDjango",
        "KbClassificationChoiceDjangoLookupType",
        "kb_classification_choice_django_lookup",
        "kb_classification_choice_django_models",
    }:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from .ClassificationChoiceDjango import ClassificationChoiceDjango

    class KbClassificationChoiceDjangoLookupType(TypedDict):
        ClassificationChoice: type[ClassificationChoiceDjango]

    exports = {
        "ClassificationChoiceDjango": ClassificationChoiceDjango,
        "KbClassificationChoiceDjangoLookupType": KbClassificationChoiceDjangoLookupType,
        "kb_classification_choice_django_lookup": KbClassificationChoiceDjangoLookupType(
            ClassificationChoice=ClassificationChoiceDjango
        ),
        "kb_classification_choice_django_models": Union[ClassificationChoiceDjango,],
    }
    globals().update(exports)
    return exports[name]
