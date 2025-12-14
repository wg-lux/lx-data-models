from typing import List, Optional, TypedDict

from pydantic import Field

from lx_dtypes.utils.factories.field_defaults import list_of_str_factory
from lx_dtypes.utils.mixins.base_model import BaseModelMixin
from lx_dtypes.utils.mixins.tags import TaggedMixin


class UnitTypeShallowDataDict(TypedDict):
    name: str
    description: str


class UnitShallowDataDict(TypedDict):
    name: str
    description: str
    abbreviation: Optional[str]
    type_names: List[str]


class UnitTypeShallow(BaseModelMixin, TaggedMixin):
    """Taggable metadata container for unit types."""

    @property
    def ddict_shallow(self) -> type[UnitTypeShallowDataDict]:
        return UnitTypeShallowDataDict

    def to_ddict_shallow(self) -> UnitTypeShallowDataDict:
        data_dict = self.ddict_shallow(**self.model_dump())
        return data_dict


class UnitShallow(BaseModelMixin):
    """
    Shallow model representing a measurement unit.
    Attributes:
        name (str): The name of the classification choice.
        name_de (str | None): The German name of the classification choice.
        name_en (str | None): The English name of the classification choice.
        description (str | None): The description of the classification choice.
        abbreviation (str | None): The abbreviation of the unit.
        type_names (list[str]): Names of associated unit types.
    """

    abbreviation: Optional[str] = None
    type_names: List[str] = Field(default_factory=list_of_str_factory)

    @property
    def ddict_shallow(self) -> type[UnitShallowDataDict]:
        return UnitShallowDataDict

    def to_ddict_shallow(self) -> UnitShallowDataDict:
        data_dict = self.ddict_shallow(**self.model_dump())
        return data_dict
