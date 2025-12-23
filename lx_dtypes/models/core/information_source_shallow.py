from typing import List

from pydantic import Field

from lx_dtypes.models.base_models.base_model import (
    KnowledgebaseBaseModel,
    KnowledgebaseBaseModelDataDict,
)
from lx_dtypes.utils.factories.field_defaults import list_of_str_factory


class InformationSourceTypeShallowDataDict(KnowledgebaseBaseModelDataDict):
    pass


class InformationSourceShallowDataDict(KnowledgebaseBaseModelDataDict):
    type_names: List[str]


class InformationSourceTypeShallow(KnowledgebaseBaseModel):
    """Simple container for information source type metadata."""

    @property
    def ddict_shallow(self) -> type[InformationSourceTypeShallowDataDict]:
        return InformationSourceTypeShallowDataDict

    def to_ddict_shallow(self) -> InformationSourceTypeShallowDataDict:
        data_dict = self.ddict_shallow(**self.model_dump())
        return data_dict


class InformationSourceShallow(KnowledgebaseBaseModel):
    """
    Shallow Model representing an information source.

    Attributes:
        name (str): The name of the classification choice.
        name_de (str | None): The German name of the classification choice.
        name_en (str | None): The English name of the classification choice.
        description (str | None): The description of the classification choice.
        types (list[str]): Names of associated information source types.
    """

    type_names: List[str] = Field(default_factory=list_of_str_factory)

    @property
    def ddict_shallow(self) -> type[InformationSourceShallowDataDict]:
        return InformationSourceShallowDataDict

    def to_ddict_shallow(self) -> InformationSourceShallowDataDict:
        data_dict = self.ddict_shallow(**self.model_dump())
        return data_dict
