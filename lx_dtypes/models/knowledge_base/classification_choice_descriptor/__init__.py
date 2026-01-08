from typing import TypedDict, Union

from .ClassificationChoiceDescriptor import (
    ClassificationChoiceDescriptor,
)
from .ClassificationChoiceDescriptorDataDict import (
    ClassificationChoiceDescriptorDataDict,
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

__all__ = [
    "ClassificationChoiceDescriptor",
    "ClassificationChoiceDescriptorDataDict",
    "kb_classification_choice_descriptor_lookup",
    "KbClassificationChoiceDescriptorLookupType",
    "kb_classification_choice_descriptor_models",
    "kb_classification_choice_descriptor_ddicts",
]
