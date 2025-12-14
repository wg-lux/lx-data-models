from typing import List, TypedDict

from pydantic import Field

from lx_dtypes.utils.factories.field_defaults import list_of_str_factory
from lx_dtypes.utils.mixins.base_model import BaseModelMixin
from lx_dtypes.utils.mixins.tags import TaggedMixin


class InterventionTypeShallowDataDict(TypedDict):
    name: str
    description: str


class InterventionShallowDataDict(TypedDict):
    name: str
    description: str
    expected_intervention_names: List[str]
    causes_finding_names: List[str]
    type_names: List[str]


class InterventionTypeShallow(BaseModelMixin, TaggedMixin):
    """Taggable shell for intervention type metadata."""

    @property
    def ddict_shallow(self) -> type[InterventionTypeShallowDataDict]:
        return InterventionTypeShallowDataDict

    def to_ddict_shallow(self) -> InterventionTypeShallowDataDict:
        data_dict = self.ddict_shallow(**self.model_dump())
        return data_dict


class InterventionShallow(BaseModelMixin):
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

    expected_intervention_names: List[str] = Field(default_factory=list_of_str_factory)
    causes_finding_names: List[str] = Field(
        default_factory=list_of_str_factory
    )  # TODO implement in source yamls
    type_names: List[str] = Field(default_factory=list_of_str_factory)

    @property
    def ddict_shallow(self) -> type[InterventionShallowDataDict]:
        return InterventionShallowDataDict

    def to_ddict_shallow(self) -> InterventionShallowDataDict:
        data_dict = self.ddict_shallow(**self.model_dump())
        return data_dict
