from typing import Dict

from pydantic import Field, field_serializer

from lx_dtypes.models.core.finding_shallow import (
    FindingShallow,
    FindingShallowDataDict,
    FindingTypeShallow,
    FindingTypeShallowDataDict,
)
from lx_dtypes.utils.factories.field_defaults import (
    classification_by_name_factory,
    finding_type_by_name_factory,
)

from .classification import Classification, ClassificationDataDict


class FindingTypeDataDict(FindingTypeShallowDataDict):
    pass


class FindingDataDict(FindingShallowDataDict):
    classifications: Dict[str, ClassificationDataDict]
    types: Dict[str, FindingTypeDataDict]


class FindingType(FindingTypeShallow):
    """Model representing a finding type."""

    @property
    def ddict(self) -> type[FindingTypeDataDict]:
        return FindingTypeDataDict

    def to_ddict(self) -> FindingTypeDataDict:
        data_dict = self.ddict(**self.model_dump())
        return data_dict


class Finding(FindingShallow):
    """Model representing a finding classification."""

    classifications: Dict[str, Classification] = Field(
        default_factory=classification_by_name_factory
    )
    types: Dict[str, FindingType] = Field(default_factory=finding_type_by_name_factory)

    @field_serializer("classifications")
    def serialize_classifications(
        self, classifications: Dict[str, "Classification"]
    ) -> Dict[str, ClassificationDataDict]:
        return {
            classification_name: classification.to_ddict()
            for classification_name, classification in classifications.items()
        }

    @field_serializer("types")
    def serialize_types(
        self, types: Dict[str, "FindingType"]
    ) -> Dict[str, FindingTypeDataDict]:
        return {
            type_name: finding_type.to_ddict()
            for type_name, finding_type in types.items()
        }

    @property
    def ddict(self) -> type[FindingDataDict]:
        return FindingDataDict

    def to_ddict(self) -> FindingDataDict:
        data_dict = self.ddict(**self.model_dump())
        return data_dict
