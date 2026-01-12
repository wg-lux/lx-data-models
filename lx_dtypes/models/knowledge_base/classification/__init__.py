from typing import TypedDict, Union

from .Classification import Classification
from .ClassificationDataDict import ClassificationDataDict
from .ClassificationDjango import ClassificationDjango
from .ClassificationType import ClassificationType
from .ClassificationTypeDataDict import ClassificationTypeDataDict
from .ClassificationTypeDjango import ClassificationTypeDjango


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
    # "ClassificationDjango",
    # "ClassificationTypeDjango",
]
