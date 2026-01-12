from typing import TypedDict, Union

from .ClassificationChoiceDescriptor import (
    ClassificationChoiceDescriptor,
)
from .ClassificationChoiceDescriptorDataDict import (
    ClassificationChoiceDescriptorDataDict,
)
from .ClassificationChoiceDescriptorDjango import (
    ClassificationChoiceDescriptorDjango,
)


class KbClassificationChoiceDescriptorDjangoLookupType(TypedDict):
    ClassificationChoiceDescriptor: type[ClassificationChoiceDescriptorDjango]


kb_classification_choice_descriptor_django_lookup = (
    KbClassificationChoiceDescriptorDjangoLookupType(
        ClassificationChoiceDescriptor=ClassificationChoiceDescriptorDjango,
    )
)


class KbClassificationChoiceDescriptorLookupType(TypedDict):
    ClassificationChoiceDescriptor: type[ClassificationChoiceDescriptor]
    ClassificationChoiceDescriptorDataDict: type[ClassificationChoiceDescriptorDataDict]


kb_classification_choice_descriptor_lookup = KbClassificationChoiceDescriptorLookupType(
    ClassificationChoiceDescriptor=ClassificationChoiceDescriptor,
    ClassificationChoiceDescriptorDataDict=ClassificationChoiceDescriptorDataDict,
)

kb_classification_choice_descriptor_models = Union[ClassificationChoiceDescriptor,]

kb_classification_choice_descriptor_ddicts = Union[
    ClassificationChoiceDescriptorDataDict,
]

kb_classification_choice_descriptor_django_models = Union[
    ClassificationChoiceDescriptorDjango,
]

__all__ = [
    "ClassificationChoiceDescriptor",
    "ClassificationChoiceDescriptorDataDict",
    "kb_classification_choice_descriptor_django_lookup",
    "KbClassificationChoiceDescriptorDjangoLookupType",
    "kb_classification_choice_descriptor_lookup",
    "KbClassificationChoiceDescriptorLookupType",
    "kb_classification_choice_descriptor_models",
    "kb_classification_choice_descriptor_ddicts",
    "kb_classification_choice_descriptor_django_models",
]
