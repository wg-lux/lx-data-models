from typing import Dict

from pydantic import Field, field_serializer

from lx_dtypes.models.core.information_source_shallow import (
    InformationSourceShallow,
    InformationSourceShallowDataDict,
    InformationSourceTypeShallow,
    InformationSourceTypeShallowDataDict,
)
from lx_dtypes.utils.factories.field_defaults import (
    information_source_type_by_name_factory,
)


class InformationSourceTypeDataDict(InformationSourceTypeShallowDataDict):
    pass


class InformationSourceDataDict(InformationSourceShallowDataDict):
    types: Dict[str, InformationSourceTypeDataDict]


class InformationSourceType(InformationSourceTypeShallow):
    """Model representing an information source type."""

    @property
    def ddict(self) -> type[InformationSourceTypeDataDict]:
        return InformationSourceTypeDataDict

    def to_ddict(self) -> InformationSourceTypeDataDict:
        data_dict = self.ddict(**self.model_dump())
        return data_dict


class InformationSource(InformationSourceShallow):
    """
    Model representing an indication using only shallow references:
    - types is a list of indication type IDs (names as str)
    """

    types: Dict[str, InformationSourceType] = Field(
        default_factory=information_source_type_by_name_factory
    )

    def _sync_shallow_fields(self) -> None:
        """Sync shallow fields from deep fields."""
        if self.types:
            self.type_names = list(self.types.keys())

    @property
    def ddict(self) -> type[InformationSourceDataDict]:
        return InformationSourceDataDict

    def to_ddict(self) -> InformationSourceDataDict:
        data_dict = self.ddict(**self.model_dump())
        return data_dict

    @field_serializer("types")
    def serialize_types(
        self, types: Dict[str, "InformationSourceType"]
    ) -> Dict[str, InformationSourceTypeDataDict]:
        return {
            type_name: information_source_type.to_ddict()
            for type_name, information_source_type in types.items()
        }

    def to_ddict_shallow(self) -> InformationSourceShallowDataDict:
        self._sync_shallow_fields()
        dump = self.model_dump()
        shallow_data = {
            key: dump[key]
            for key in self.ddict_shallow.__annotations__.keys()
            if key in dump
        }

        return self.ddict_shallow(**shallow_data)
