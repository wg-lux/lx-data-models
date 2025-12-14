from typing import List, TypedDict

from pydantic import Field

from lx_dtypes.utils.factories.field_defaults import list_of_str_factory
from lx_dtypes.utils.mixins.base_model import BaseModelMixin
from lx_dtypes.utils.mixins.tags import TaggedMixin


class InformationSourceTypeShallowDataDict(TypedDict):
    name: str
    description: str


class InformationSourceShallowDataDict(TypedDict):
    name: str
    description: str
    type_names: List[str]


class InformationSourceTypeShallow(BaseModelMixin, TaggedMixin):
    """Simple container for information source type metadata."""

    @property
    def ddict_shallow(self) -> type[InformationSourceTypeShallowDataDict]:
        return InformationSourceTypeShallowDataDict

    def to_ddict_shallow(self) -> InformationSourceTypeShallowDataDict:
        data_dict = self.ddict_shallow(**self.model_dump())
        return data_dict


class InformationSourceShallow(BaseModelMixin, TaggedMixin):
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
