from typing import TypedDict, Union

from ._ClassificationDjango import ClassificationDjango
from ._ClassificationTypeDjango import ClassificationTypeDjango
from .Classification import Classification
from .ClassificationDataDict import ClassificationDataDict
from .ClassificationType import ClassificationType
from .ClassificationTypeDataDict import ClassificationTypeDataDict


class KbClassificationDjangoLookupType(TypedDict):
    Classification: type["ClassificationDjango"]
    ClassificationType: type["ClassificationTypeDjango"]


kb_classification_django_lookup = KbClassificationDjangoLookupType(
    Classification=ClassificationDjango,
    ClassificationType=ClassificationTypeDjango,
)


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

kb_classification_django_models = Union[
    ClassificationDjango,
    ClassificationTypeDjango,
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
    "kb_classification_django_models",
    "kb_classification_django_lookup",
    "ClassificationDjango",
    "ClassificationTypeDjango",
]
