from typing import TYPE_CHECKING, List, Self

from django.db import models

from lx_dtypes.models.core.unit import (
    UnitDataDict,
    UnitTypeDataDict,
)
from lx_dtypes.models.core.unit_shallow import (
    UnitShallowDataDict,
    UnitTypeShallowDataDict,
)

from ..base_model.base_model import KnowledgebaseBaseModel
from ..typing import OptionalCharFieldType

if TYPE_CHECKING:
    from .classification_choice_descriptor import ClassificationChoiceDescriptor


class UnitType(KnowledgebaseBaseModel):
    if TYPE_CHECKING:
        units: models.Manager["Unit"]

    @property
    def ddict_shallow(self) -> type[UnitTypeShallowDataDict]:
        return UnitTypeShallowDataDict

    @property
    def ddict(self) -> type[UnitTypeDataDict]:
        return UnitTypeDataDict

    @classmethod
    def sync_from_ddict_shallow(cls, ddict: UnitTypeShallowDataDict) -> Self:
        """Create a UnitType model instance from a UnitTypeShallowDataDict.

        Args:
            ddict (UnitTypeShallowDataDict): The data dictionary to create the model instance from.
        Returns:
            UnitType: The created UnitType model instance.
        """
        obj = cls.objects.create(**ddict)
        return obj

    def to_ddict_shallow(self) -> UnitTypeShallowDataDict:
        """Convert the UnitType model instance to a UnitTypeShallowDataDict.

        Returns:
            UnitTypeShallowDataDict: The converted data dictionary.
        """
        data_dict = self._to_ddict()
        ddict = self.ddict_shallow(**data_dict)
        return ddict


class Unit(KnowledgebaseBaseModel):
    types: models.ManyToManyField["UnitType", "UnitType"] = models.ManyToManyField(
        "UnitType",
        related_name="units",
        blank=True,
    )

    abbreviation: OptionalCharFieldType = models.CharField(
        max_length=100, null=True, blank=True
    )

    if TYPE_CHECKING:
        classification_choice_descriptors: models.Manager[
            "ClassificationChoiceDescriptor"
        ]

    @property
    def ddict_shallow(self) -> type[UnitShallowDataDict]:
        return UnitShallowDataDict

    @property
    def ddict(self) -> type[UnitDataDict]:
        return UnitDataDict

    @classmethod
    def sync_from_ddict_shallow(cls, ddict: UnitShallowDataDict) -> Self:
        """Create a Unit model instance from a UnitShallowDataDict.

        Args:
            ddict (UnitShallowDataDict): The data dictionary to create the model instance from.
        Returns:
            Unit: The created Unit model instance.
        """
        type_names = ddict["type_names"]
        defaults = dict(ddict)
        defaults.pop("type_names", None)

        # check if with same uuid already exists
        obj, created = cls.objects.get_or_create(uuid=ddict["uuid"], defaults=defaults)

        if not created:
            for key, value in ddict.items():
                setattr(obj, key, value)

        obj.update_types_by_names(type_names)

        return obj

    # def sync_to_ddict_shallow(self, ddict: UnitShallowDataDict) -> UnitShallowDataDict:
    #     """
    #     Sync the Unit model instance to a UnitShallowDataDict.
    #     Args:
    #         ddict (UnitShallowDataDict): The data dictionary to sync the model instance to.
    #     """
    #     data_dict = self.to_ddict_shallow()
    #     assert data_dict["uuid"] == ddict["uuid"]

    #     for key, value in data_dict.items():
    #         ddict[key] = value
    #     return ddict

    def update_types_by_names(self, type_names: List[str]) -> None:
        """Update the types of the Unit model instance based on a list of type names.

        Args:
            type_names (List[str]): The list of type names to update the types.
        """
        unit_types: List[UnitType] = []

        for unit_type in type_names:
            try:
                unit_types.append(UnitType.get_by_name(unit_type))
            except UnitType.DoesNotExist:
                raise ValueError(f"UnitType with name '{unit_type}' does not exist.")

        self.types.set(unit_types)
        self.save()

    def to_ddict_shallow(self) -> UnitShallowDataDict:
        """Convert the Classification model instance to a ClassificationShallowDataDict.

        Returns:
            ClassificationShallowDataDict: The converted data dictionary.
        """
        data_dict = self._to_ddict()

        # Serialize types
        data_dict.pop("types", None)
        type_names = [ut.name for ut in self.types.all()]
        data_dict["type_names"] = type_names

        ddict = self.ddict_shallow(**data_dict)
        return ddict
