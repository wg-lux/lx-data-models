from typing import List

from pydantic import Field, field_serializer

from lx_dtypes.models.core.classification_choice_shallow import (
    ClassificationChoiceShallow,
    ClassificationChoiceShallowDataDict,
)
from lx_dtypes.utils.factories.field_defaults import (
    list_of_classification_choice_descriptor_factory,
)

from .classification_choice_descriptor import (
    ClassificationChoiceDescriptor,
    ClassificationChoiceDescriptorDataDict,
)


class ClassificationChoiceDataDict(ClassificationChoiceShallowDataDict):
    classification_choice_descriptors: List[ClassificationChoiceDescriptorDataDict]


class ClassificationChoice(ClassificationChoiceShallow):
    """Model representing a classification choice."""

    classification_choice_descriptors: List[ClassificationChoiceDescriptor] = Field(
        default_factory=list_of_classification_choice_descriptor_factory
    )

    @property
    def ddict(self) -> type[ClassificationChoiceDataDict]:
        return ClassificationChoiceDataDict

    @field_serializer("classification_choice_descriptors")
    def serialize_classification_choice_descriptors(
        self, classification_choice_descriptors: List[ClassificationChoiceDescriptor]
    ) -> List[ClassificationChoiceDescriptorDataDict]:
        return [
            descriptor.to_ddict() for descriptor in classification_choice_descriptors
        ]

    def to_ddict(self) -> ClassificationChoiceDataDict:
        data_dict = self.ddict(**self.model_dump())
        return data_dict
