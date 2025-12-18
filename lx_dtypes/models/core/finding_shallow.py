from typing import List

from pydantic import Field

from lx_dtypes.models.base_models.base_model import (
    AppBaseModelNamesUUIDTags,
    AppBaseModelNamesUUIDTagsDataDict,
)
from lx_dtypes.utils.factories.field_defaults import list_of_str_factory


class FindingTypeShallowDataDict(AppBaseModelNamesUUIDTagsDataDict):
    pass


class FindingShallowDataDict(AppBaseModelNamesUUIDTagsDataDict):
    classification_names: List[str]
    type_names: List[str]
    intervention_names: List[str]


class FindingTypeShallow(AppBaseModelNamesUUIDTags):
    """Metadata shell for finding types."""

    @property
    def ddict_shallow(self) -> type[FindingTypeShallowDataDict]:
        return FindingTypeShallowDataDict

    def to_ddict_shallow(self) -> FindingTypeShallowDataDict:
        data_dict = self.ddict_shallow(**self.model_dump())
        return data_dict


class FindingShallow(AppBaseModelNamesUUIDTags):
    """
    Shallow model representing a medical finding.

    Attributes:
        name (str): The name of the classification choice.
        name_de (str | None): The German name of the classification choice.
        name_en (str | None): The English name of the classification choice.
        description (str | None): The description of the classification choice.
        classification_names (list[str]): Names of associated classifications.
        type_names (list[str]): Names of associated finding types.
        intervention_names (list[str]): Names of associated interventions.

    """

    classification_names: List[str] = Field(default_factory=list_of_str_factory)
    type_names: List[str] = Field(default_factory=list_of_str_factory)
    intervention_names: List[str] = Field(default_factory=list_of_str_factory)

    @property
    def ddict_shallow(self) -> type[FindingShallowDataDict]:
        return FindingShallowDataDict

    def to_ddict_shallow(self) -> FindingShallowDataDict:
        data_dict = self.ddict_shallow(**self.model_dump())
        return data_dict
