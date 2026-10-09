from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeAlias, TypedDict

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

kb_classification_choice_models: TypeAlias = ClassificationChoice

kb_classification_choice_ddicts: TypeAlias = ClassificationChoiceDataDict

if TYPE_CHECKING:

    class KbClassificationChoiceDjangoLookupType(TypedDict):
        ClassificationChoice: type[ClassificationChoiceDjango]

    kb_classification_choice_django_lookup: KbClassificationChoiceDjangoLookupType
    kb_classification_choice_django_models: TypeAlias = ClassificationChoiceDjango

__all__ = [
    "ClassificationChoice",
    "ClassificationChoiceDataDict",
    "KbClassificationChoiceDjangoLookupType",
    "KbClassificationChoiceLookupType",
    "kb_classification_choice_ddicts",
    "kb_classification_choice_django_lookup",
    "kb_classification_choice_django_models",
    "kb_classification_choice_lookup",
    "kb_classification_choice_models",
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
        "kb_classification_choice_django_models": ClassificationChoiceDjango,
    }
    globals().update(exports)
    return exports[name]
