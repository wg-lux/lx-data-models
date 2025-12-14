from typing import List, TypedDict, Union

from pydantic import Field, field_serializer

from lx_dtypes.models.shallow.unit import (
    UnitShallow,
    UnitTypeShallow,
)
from lx_dtypes.utils.factories.field_defaults import list_of_unit_types_factory


class UnitTypeDataDict(TypedDict):
    name: str
    name_de: Union[str, None]
    name_en: Union[str, None]
    description: Union[str, None]


class UnitDataDict(TypedDict):
    name: str
    name_de: Union[str, None]
    name_en: Union[str, None]
    description: Union[str, None]
    abbreviation: Union[str, None]
    types: List[UnitTypeDataDict]


class UnitType(UnitTypeShallow):
    @property
    def ddict(self) -> type[UnitTypeDataDict]:
        return UnitTypeDataDict

    def to_ddict(self) -> UnitTypeDataDict:
        data_dict = self.ddict(**self.model_dump())
        return data_dict


class Unit(UnitShallow):
    types: list[UnitType] = Field(default_factory=list_of_unit_types_factory)

    @property
    def ddict(self) -> type[UnitDataDict]:
        return UnitDataDict

    @field_serializer("types")
    def serialize_types(self, types: list[UnitType]) -> List[UnitTypeDataDict]:
        result = [unit_type.to_ddict() for unit_type in types]
        return result

    def to_ddict(self) -> UnitDataDict:
        data_dict = self.ddict(**self.model_dump())
        return data_dict
