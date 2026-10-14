from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeAlias, TypedDict, Union

from .Classification import Classification
from .ClassificationDataDict import ClassificationDataDict
from .ClassificationType import ClassificationType
from .ClassificationTypeDataDict import ClassificationTypeDataDict

if TYPE_CHECKING:
    from ._ClassificationDjango import ClassificationDjango
    from ._ClassificationTypeDjango import ClassificationTypeDjango


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

kb_classification_models: TypeAlias = Union[Classification, ClassificationType]

kb_classification_ddicts: TypeAlias = Union[
    ClassificationDataDict, ClassificationTypeDataDict
]

if TYPE_CHECKING:

    class KbClassificationDjangoLookupType(TypedDict):
        Classification: type[ClassificationDjango]
        ClassificationType: type[ClassificationTypeDjango]

    kb_classification_django_lookup: KbClassificationDjangoLookupType
    kb_classification_django_models: TypeAlias = Union[
        ClassificationDjango, ClassificationTypeDjango
    ]


__all__ = [
    "Classification",
    "ClassificationDataDict",
    "ClassificationDjango",
    "ClassificationType",
    # "ClassificationChoicesMixin",
    "ClassificationTypeDataDict",
    "ClassificationTypeDjango",
    "KbClassificationLookupType",
    "kb_classification_ddicts",
    "kb_classification_django_lookup",
    "kb_classification_django_models",
    # "ClassificationTypesMixin",
    "kb_classification_lookup",
    "kb_classification_models",
]


def __getattr__(name: str) -> Any:
    if name not in {
        "ClassificationDjango",
        "ClassificationTypeDjango",
        "KbClassificationDjangoLookupType",
        "kb_classification_django_lookup",
        "kb_classification_django_models",
    }:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from ._ClassificationDjango import ClassificationDjango
    from ._ClassificationTypeDjango import ClassificationTypeDjango

    class KbClassificationDjangoLookupType(TypedDict):
        Classification: type[ClassificationDjango]
        ClassificationType: type[ClassificationTypeDjango]

    exports = {
        "ClassificationDjango": ClassificationDjango,
        "ClassificationTypeDjango": ClassificationTypeDjango,
        "KbClassificationDjangoLookupType": KbClassificationDjangoLookupType,
        "kb_classification_django_lookup": KbClassificationDjangoLookupType(
            Classification=ClassificationDjango,
            ClassificationType=ClassificationTypeDjango,
        ),
        "kb_classification_django_models": (
            ClassificationDjango | ClassificationTypeDjango
        ),
    }
    globals().update(exports)
    return exports[name]
