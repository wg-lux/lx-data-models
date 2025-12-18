from django.db import models

from lx_dtypes.models.core.unit import (
    UnitDataDict,
    UnitTypeDataDict,
)
from lx_dtypes.models.core.unit_shallow import (
    UnitShallowDataDict,
    UnitTypeShallowDataDict,
)

from ..base_model.base_model import AppBaseModelNamesUUIDTags
from ..typing import CharFieldType, OptionalCharFieldType


class UnitType(AppBaseModelNamesUUIDTags):
    @property
    def ddict_shallow(self) -> type[UnitTypeShallowDataDict]:
        return UnitTypeShallowDataDict

    @property
    def ddict(self) -> type[UnitTypeDataDict]:
        return UnitTypeDataDict


class Unit(AppBaseModelNamesUUIDTags):
    abbreviation: OptionalCharFieldType = models.CharField(
        max_length=100, null=True, blank=True
    )
    type_names: CharFieldType = models.CharField(
        max_length=2000, null=True, blank=True
    )  # store as comma-separated UUIDs

    @property
    def ddict_shallow(self) -> type[UnitShallowDataDict]:
        return UnitShallowDataDict

    @property
    def ddict(self) -> type[UnitDataDict]:
        return UnitDataDict

    def to_ddict_shallow(self) -> UnitShallowDataDict:
        """Convert the Classification model instance to a ClassificationShallowDataDict.

        Returns:
            ClassificationShallowDataDict: The converted data dictionary.
        """
        data_dict = self._to_ddict()
        data_dict["type_names"] = self.str_list_to_list(self.type_names)

        ddict = self.ddict_shallow(**data_dict)
        return ddict
