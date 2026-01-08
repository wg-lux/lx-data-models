from typing import TypedDict, Union

from .Classification import Classification
from .ClassificationDataDict import ClassificationDataDict
from .ClassificationType import ClassificationType
from .ClassificationTypeDataDict import ClassificationTypeDataDict


class KbClassificationLookupType(TypedDict):
    Classification: type[Classification]
    ClassificationDataDict: type[ClassificationDataDict]
    ClassificationType: type[ClassificationType]
    ClassificationTypeDataDict: type[ClassificationTypeDataDict]


kb_classification_lookup = KbClassificationLookupType(
    Classification=Classification,
    ClassificationDataDict=ClassificationDataDict,
    ClassificationType=ClassificationType,
    ClassificationTypeDataDict=ClassificationTypeDataDict,
)

kb_classification_models = Union[
    Classification,
    ClassificationType,
]

kb_classification_ddicts = Union[
    ClassificationDataDict,
    ClassificationTypeDataDict,
]


__all__ = [
    "Classification",
    "ClassificationDataDict",
    "ClassificationType",
    # "ClassificationChoicesMixin",
    "ClassificationTypeDataDict",
    # "ClassificationTypesMixin",
    "kb_classification_lookup",
    "KbClassificationLookupType",
    "kb_classification_models",
    "kb_classification_ddicts",
]
