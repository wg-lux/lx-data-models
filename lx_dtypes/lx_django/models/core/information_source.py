from typing import TYPE_CHECKING

from django.db import models

from lx_dtypes.models.core.information_source import (
    InformationSourceDataDict,
    InformationSourceTypeDataDict,
)
from lx_dtypes.models.core.information_source_shallow import (
    InformationSourceShallowDataDict,
    InformationSourceTypeShallowDataDict,
)

from ..base_model.base_model import KnowledgebaseBaseModel
from ..typing import (
    OptionalCharFieldType,
)


class InformationSourceType(KnowledgebaseBaseModel):
    if TYPE_CHECKING:
        information_sources: models.Manager["InformationSource"]

    @property
    def ddict_shallow(self) -> type[InformationSourceTypeShallowDataDict]:
        return InformationSourceTypeShallowDataDict

    @property
    def ddict(self) -> type[InformationSourceTypeDataDict]:
        return InformationSourceTypeDataDict

    @classmethod
    def sync_from_ddict_shallow(
        cls, ddict: InformationSourceTypeShallowDataDict
    ) -> "InformationSourceType":
        """Create an InformationSourceType model instance from an InformationSourceTypeShallowDataDict.

        Args:
            ddict (InformationSourceTypeShallowDataDict): The data dictionary to create the model instance from.
        Returns:
            InformationSourceType: The created InformationSourceType model instance.
        """

        obj, created = cls.objects.get_or_create(uuid=ddict["uuid"], defaults=ddict)
        if not created:
            for key, value in ddict.items():
                setattr(obj, key, value)
            obj.save()

        return obj


class InformationSource(KnowledgebaseBaseModel):
    types: models.ManyToManyField["InformationSourceType", "InformationSourceType"] = (
        models.ManyToManyField(
            "InformationSourceType",
            related_name="information_sources",
            blank=True,
        )
    )
    type_names: OptionalCharFieldType = models.CharField(
        max_length=2000, null=True, blank=True
    )  # store as comma-separated UUIDs

    @property
    def ddict_shallow(self) -> type[InformationSourceShallowDataDict]:
        return InformationSourceShallowDataDict

    @property
    def ddict(self) -> type[InformationSourceDataDict]:
        return InformationSourceDataDict

    @classmethod
    def sync_from_ddict_shallow(
        cls, ddict: InformationSourceShallowDataDict
    ) -> "InformationSource":
        """Create an InformationSource model instance from an InformationSourceShallowDataDict.

        Args:
            ddict (InformationSourceShallowDataDict): The data dictionary to create the model instance from.
        Returns:
            InformationSource: The created InformationSource model instance.
        """
        type_names = ddict["type_names"]
        # cast ddict to Dict[str, Any] to allow pop
        defaults = dict(ddict)
        defaults.pop("type_names", None)

        # check if with same uuid already exists
        obj, created = cls.objects.get_or_create(uuid=ddict["uuid"], defaults=defaults)

        if not created:
            for key, value in ddict.items():
                setattr(obj, key, value)

        obj.type_names = ",".join(type_names)
        obj.save()

        return obj

    def to_ddict_shallow(self) -> InformationSourceShallowDataDict:
        """Convert the InformationSource model instance to a InformationSourceShallowDataDict.

        Returns:
            InformationSourceShallowDataDict: The converted data dictionary.
        """
        data_dict = self._to_ddict()
        data_dict["type_names"] = self.str_list_to_list(self.type_names)

        ddict = self.ddict_shallow(**data_dict)
        return ddict
