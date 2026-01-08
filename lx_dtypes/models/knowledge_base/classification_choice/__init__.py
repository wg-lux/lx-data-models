from typing import TypedDict, Union

from .ClassificationChoice import ClassificationChoice
from .ClassificationChoiceDataDict import ClassificationChoiceDataDict


class KbClassificationChoiceLookupType(TypedDict):
    ClassificationChoice: type[ClassificationChoice]
    ClassificationChoiceDataDict: type[ClassificationChoiceDataDict]


kb_classification_choice_lookup = KbClassificationChoiceLookupType(
    ClassificationChoice=ClassificationChoice,
    ClassificationChoiceDataDict=ClassificationChoiceDataDict,
)

kb_classification_choice_models = Union[ClassificationChoice,]

kb_classification_choice_ddicts = Union[ClassificationChoiceDataDict,]

__all__ = [
    "ClassificationChoice",
    "ClassificationChoiceDataDict",
    "kb_classification_choice_lookup",
    "KbClassificationChoiceLookupType",
    "kb_classification_choice_models",
    "kb_classification_choice_ddicts",
]
