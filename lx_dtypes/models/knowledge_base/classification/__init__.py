from typing import TypedDict

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


__all__ = [
    "Classification",
    "ClassificationDataDict",
    "ClassificationType",
    # "ClassificationChoicesMixin",
    "ClassificationTypeDataDict",
    # "ClassificationTypesMixin",
    "kb_classification_lookup",
    "KbClassificationLookupType",
]
