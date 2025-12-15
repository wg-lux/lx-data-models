from typing import Optional

from pydantic import field_serializer

from lx_dtypes.models.core.unit import Unit, UnitDataDict
from lx_dtypes.models.shallow.classification_choice_descriptor import (
    ClassificationChoiceDescriptorShallow,
    ClassificationChoiceDescriptorShallowDataDict,
)


class ClassificationChoiceDescriptorDataDict(
    ClassificationChoiceDescriptorShallowDataDict
):
    unit: Optional[UnitDataDict]


class ClassificationChoiceDescriptor(ClassificationChoiceDescriptorShallow):
    unit: Optional[Unit]

    @property
    def ddict(self) -> type[ClassificationChoiceDescriptorDataDict]:
        return ClassificationChoiceDescriptorDataDict

    @field_serializer("unit")
    def serialize_unit(self, unit: Optional[Unit]) -> Optional[UnitDataDict]:
        if unit is None:
            return None
        return unit.to_ddict()

    def to_ddict(self) -> ClassificationChoiceDescriptorDataDict:
        data_dict = self.ddict(**self.model_dump())
        return data_dict

    def to_ddict_shallow(
        self,
    ) -> ClassificationChoiceDescriptorShallowDataDict:
        dump = self.model_dump()
        shallow_data = {
            key: dump[key]
            for key in self.ddict_shallow.__annotations__.keys()
            if key in dump
        }
        return self.ddict_shallow(**shallow_data)
