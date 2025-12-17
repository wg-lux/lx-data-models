from typing import Dict

from pydantic import Field, field_serializer

from lx_dtypes.models.core.indication_shallow import (
    IndicationShallow,
    IndicationShallowDataDict,
    IndicationTypeShallow,
    IndicationTypeShallowDataDict,
)
from lx_dtypes.utils.factories.field_defaults import indication_type_by_name_factory


class IndicationTypeDataDict(IndicationTypeShallowDataDict):
    pass


class IndicationDataDict(IndicationShallowDataDict):
    types: Dict[str, IndicationTypeDataDict]


class IndicationType(IndicationTypeShallow):
    """Model representing an indication type."""

    @property
    def ddict(self) -> type[IndicationTypeDataDict]:
        return IndicationTypeDataDict

    def to_ddict(self) -> IndicationTypeDataDict:
        data_dict = self.ddict(**self.model_dump())
        return data_dict


class Indication(IndicationShallow):
    """Model representing an indication."""

    types: Dict[str, IndicationType] = Field(
        default_factory=indication_type_by_name_factory
    )

    @field_serializer("types")
    def serialize_types(
        self, types: Dict[str, "IndicationType"]
    ) -> Dict[str, IndicationTypeDataDict]:
        return {
            type_name: indication_type.to_ddict()
            for type_name, indication_type in types.items()
        }

    @property
    def ddict(self) -> type[IndicationDataDict]:
        return IndicationDataDict

    def to_ddict(self) -> IndicationDataDict:
        data_dict = self.ddict(**self.model_dump())
        return data_dict
