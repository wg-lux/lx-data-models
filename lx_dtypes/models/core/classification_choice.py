from typing import List

from pydantic import Field

from lx_dtypes.models.shallow.classification_choice import ClassificationChoiceShallow
from lx_dtypes.utils.factories.field_defaults import list_of_classification_choice_descriptor_factory

from .classification_choice_descriptor import ClassificationChoiceDescriptor


class ClassificationChoice(ClassificationChoiceShallow):
    """Model representing a classification choice."""

    classification_choice_descriptors: List[ClassificationChoiceDescriptor] = Field(default_factory=list_of_classification_choice_descriptor_factory)
