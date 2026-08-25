from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeAlias, TypedDict

from .ClassificationChoiceDescriptor import (
    ClassificationChoiceDescriptor,
)
from .ClassificationChoiceDescriptorDataDict import (
    ClassificationChoiceDescriptorDataDict,
)

if TYPE_CHECKING:
    from .ClassificationChoiceDescriptorDjango import (
        ClassificationChoiceDescriptorDjango,
    )


class KbClassificationChoiceDescriptorLookupType(TypedDict):
    ClassificationChoiceDescriptor: type[ClassificationChoiceDescriptor]
    ClassificationChoiceDescriptorDataDict: type[ClassificationChoiceDescriptorDataDict]


kb_classification_choice_descriptor_lookup = KbClassificationChoiceDescriptorLookupType(
    ClassificationChoiceDescriptor=ClassificationChoiceDescriptor,
    ClassificationChoiceDescriptorDataDict=ClassificationChoiceDescriptorDataDict,
)

kb_classification_choice_descriptor_models: TypeAlias = ClassificationChoiceDescriptor

kb_classification_choice_descriptor_ddicts: TypeAlias = (
    ClassificationChoiceDescriptorDataDict
)

if TYPE_CHECKING:

    class KbClassificationChoiceDescriptorDjangoLookupType(TypedDict):
        ClassificationChoiceDescriptor: type[ClassificationChoiceDescriptorDjango]

    kb_classification_choice_descriptor_django_lookup: (
        KbClassificationChoiceDescriptorDjangoLookupType
    )
    kb_classification_choice_descriptor_django_models: TypeAlias = (
        ClassificationChoiceDescriptorDjango
    )

__all__ = [
    "ClassificationChoiceDescriptor",
    "ClassificationChoiceDescriptorDataDict",
    "KbClassificationChoiceDescriptorDjangoLookupType",
    "KbClassificationChoiceDescriptorLookupType",
    "kb_classification_choice_descriptor_ddicts",
    "kb_classification_choice_descriptor_django_lookup",
    "kb_classification_choice_descriptor_django_models",
    "kb_classification_choice_descriptor_lookup",
    "kb_classification_choice_descriptor_models",
]


def __getattr__(name: str) -> Any:
    if name not in {
        "ClassificationChoiceDescriptorDjango",
        "KbClassificationChoiceDescriptorDjangoLookupType",
        "kb_classification_choice_descriptor_django_lookup",
        "kb_classification_choice_descriptor_django_models",
    }:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from .ClassificationChoiceDescriptorDjango import (
        ClassificationChoiceDescriptorDjango,
    )

    class KbClassificationChoiceDescriptorDjangoLookupType(TypedDict):
        ClassificationChoiceDescriptor: type[ClassificationChoiceDescriptorDjango]

    exports = {
        "ClassificationChoiceDescriptorDjango": ClassificationChoiceDescriptorDjango,
        "KbClassificationChoiceDescriptorDjangoLookupType": KbClassificationChoiceDescriptorDjangoLookupType,
        "kb_classification_choice_descriptor_django_lookup": KbClassificationChoiceDescriptorDjangoLookupType(
            ClassificationChoiceDescriptor=ClassificationChoiceDescriptorDjango
        ),
        "kb_classification_choice_descriptor_django_models": (
            ClassificationChoiceDescriptorDjango
        ),
    }
    globals().update(exports)
    return exports[name]
