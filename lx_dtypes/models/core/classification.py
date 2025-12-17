from typing import Dict

from pydantic import Field

from lx_dtypes.models.core.classification_shallow import (
    ClassificationShallow,
    ClassificationShallowDataDict,
    ClassificationTypeShallow,
    ClassificationTypeShallowDataDict,
)

from .classification_choice import ClassificationChoice, ClassificationChoiceDataDict


class ClassificationTypeDataDict(ClassificationTypeShallowDataDict):
    pass


class ClassificationDataDict(ClassificationShallowDataDict):
    classification_choices: Dict[str, ClassificationChoiceDataDict]
    types: Dict[str, ClassificationTypeDataDict]


class ClassificationType(ClassificationTypeShallow):
    """Model representing a classification type."""

    @property
    def ddict(self) -> type[ClassificationTypeDataDict]:
        return ClassificationTypeDataDict

    def to_ddict(self) -> ClassificationTypeDataDict:
        data_dict = self.ddict(**self.model_dump())
        return data_dict


class Classification(ClassificationShallow):
    """Model representing a finding classification."""

    classification_choices: Dict[str, ClassificationChoice] = Field(
        default_factory=dict
    )
    types: Dict[str, ClassificationType] = Field(default_factory=dict)

    @property
    def ddict(self) -> type[ClassificationDataDict]:
        return ClassificationDataDict

    def to_ddict(self) -> ClassificationDataDict:
        data_dict = self.ddict(**self.model_dump())
        return data_dict
