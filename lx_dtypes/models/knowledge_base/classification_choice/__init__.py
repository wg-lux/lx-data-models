from typing import TypedDict, Union

from .ClassificationChoice import ClassificationChoice
from .ClassificationChoiceDataDict import ClassificationChoiceDataDict
from .ClassificationChoiceDjango import ClassificationChoiceDjango


class KbClassificationChoiceDjangoLookupType(TypedDict):
    ClassificationChoice: type[ClassificationChoiceDjango]


kb_classification_choice_django_lookup = KbClassificationChoiceDjangoLookupType(
    ClassificationChoice=ClassificationChoiceDjango,
)


class KbClassificationChoiceLookupType(TypedDict):
    ClassificationChoice: type[ClassificationChoice]
    ClassificationChoiceDataDict: type[ClassificationChoiceDataDict]


kb_classification_choice_lookup = KbClassificationChoiceLookupType(
    ClassificationChoice=ClassificationChoice,
    ClassificationChoiceDataDict=ClassificationChoiceDataDict,
)

kb_classification_choice_models = Union[ClassificationChoice,]

kb_classification_choice_ddicts = Union[ClassificationChoiceDataDict,]

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
