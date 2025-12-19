from typing import List

from pydantic import Field

from lx_dtypes.models.base_models.base_model import (
    KnowledgeBaseModel,
    KnowledgeBaseModelDataDict,
)
from lx_dtypes.utils.factories.field_defaults import list_of_str_factory


class IndicationTypeShallowDataDict(KnowledgeBaseModelDataDict):
    pass


class IndicationShallowDataDict(KnowledgeBaseModelDataDict):
    type_names: List[str]
    expected_intervention_names: List[str]


class IndicationTypeShallow(KnowledgeBaseModel):
    """Taggable metadata container for indication types."""

    @property
    def ddict_shallow(self) -> type[IndicationTypeShallowDataDict]:
        return IndicationTypeShallowDataDict

    def to_ddict_shallow(self) -> IndicationTypeShallowDataDict:
        data_dict = self.ddict_shallow(**self.model_dump())
        return data_dict


class IndicationShallow(KnowledgeBaseModel):
    """
    Shallow model representing a medical indication.

    Attributes:
        name (str): The name of the classification choice.
        name_de (str | None): The German name of the classification choice.
        name_en (str | None): The English name of the classification choice.
        description (str | None): The description of the classification choice.
        type_names (list[str]): Names of associated indication types.
        expected_intervention_names (list[str]): Names of expected interventions.

    """

    type_names: List[str] = Field(default_factory=list_of_str_factory)
    expected_intervention_names: List[str] = Field(default_factory=list_of_str_factory)

    @property
    def ddict_shallow(self) -> type[IndicationShallowDataDict]:
        return IndicationShallowDataDict

    def to_ddict_shallow(self) -> IndicationShallowDataDict:
        data_dict = self.ddict_shallow(**self.model_dump())
        return data_dict
