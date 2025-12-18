from typing import List

from pydantic import Field

from lx_dtypes.models.base_models.base_model import (
    AppBaseModelNamesUUIDTags,
    AppBaseModelNamesUUIDTagsDataDict,
)
from lx_dtypes.utils.factories.field_defaults import list_of_str_factory


class InterventionTypeShallowDataDict(AppBaseModelNamesUUIDTagsDataDict):
    pass


class InterventionShallowDataDict(AppBaseModelNamesUUIDTagsDataDict):
    type_names: List[str]


class InterventionTypeShallow(AppBaseModelNamesUUIDTags):
    """Taggable shell for intervention type metadata."""

    @property
    def ddict_shallow(self) -> type[InterventionTypeShallowDataDict]:
        return InterventionTypeShallowDataDict

    def to_ddict_shallow(self) -> InterventionTypeShallowDataDict:
        data_dict = self.ddict_shallow(**self.model_dump())
        return data_dict


class InterventionShallow(AppBaseModelNamesUUIDTags):
    """
    Shallow Model to represent a medical intervention.
    Attributes:
        name (str): The name of the classification choice.
        name_de (str | None): The German name of the classification choice.
        name_en (str | None): The English name of the classification choice.
        description (str | None): The description of the classification choice.
        expected_intervention_names (list[str]): Names of expected interventions.
        causes_finding_names (list[str]): Names of findings caused by this intervention.
        type_names (list[str]): Names of associated intervention types.
    """

    type_names: List[str] = Field(default_factory=list_of_str_factory)

    @property
    def ddict_shallow(self) -> type[InterventionShallowDataDict]:
        return InterventionShallowDataDict

    def to_ddict_shallow(self) -> InterventionShallowDataDict:
        data_dict = self.ddict_shallow(**self.model_dump())
        return data_dict
