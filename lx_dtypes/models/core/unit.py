from typing import List

from pydantic import Field, field_serializer

from lx_dtypes.models.core.unit_shallow import (
    UnitShallow,
    UnitShallowDataDict,
    UnitTypeShallow,
    UnitTypeShallowDataDict,
)
from lx_dtypes.utils.factories.field_defaults import list_of_unit_types_factory


class UnitTypeDataDict(UnitTypeShallowDataDict):
    pass


class UnitDataDict(UnitShallowDataDict):
    pass
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

    def _sync_shallow_fields(self) -> None:
        """Sync shallow fields from deep fields."""
        if self.types:
            self.type_names = [unit_type.name for unit_type in self.types]

    def to_ddict(self) -> UnitDataDict:
        data_dict = self.ddict(**self.model_dump())
        return data_dict

    def to_ddict_shallow(self) -> UnitShallowDataDict:
        self._sync_shallow_fields()
        dump = self.model_dump()
        shallow_data = {
            key: dump[key]
            for key in self.ddict_shallow.__annotations__.keys()
            if key in dump
        }
        return self.ddict_shallow(**shallow_data)
