from typing import Dict

from pydantic import Field

from lx_dtypes.models.shallow.classification import ClassificationShallow, ClassificationTypeShallow

from .classification_choice import ClassificationChoice


class ClassificationType(ClassificationTypeShallow):
    pass


class Classification(ClassificationShallow):
    """Model representing a finding classification."""

    classification_choices: Dict[str, ClassificationChoice] = Field(default_factory=dict)
    types: Dict[str, ClassificationType] = Field(default_factory=dict)
