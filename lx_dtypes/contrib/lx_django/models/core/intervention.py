from typing import TYPE_CHECKING

from django.db import models

from lx_dtypes.models.core.intervention import (
    InterventionDataDict,
    InterventionTypeDataDict,
)
from lx_dtypes.models.core.intervention_shallow import (
    InterventionShallowDataDict,
    InterventionTypeShallowDataDict,
)

from ..base_model.base_model import KnowledgebaseBaseModel

if TYPE_CHECKING:
    from .finding import Finding
    from .indication import Indication


class InterventionType(KnowledgebaseBaseModel):
    if TYPE_CHECKING:
        interventions: models.Manager["Intervention"]

    @property
    def ddict_shallow(self) -> type[InterventionTypeShallowDataDict]:
        return InterventionTypeShallowDataDict

    @property
    def ddict(self) -> type[InterventionTypeDataDict]:
        return InterventionTypeDataDict

    @classmethod
    def sync_from_ddict_shallow(
        cls, ddict: InterventionTypeShallowDataDict
    ) -> "InterventionType":
        """Create an InterventionType model instance from an InterventionTypeShallowDataDict.

        Args:
            ddict (InterventionTypeShallowDataDict): The data dictionary to create the model instance from.
        Returns:
            InterventionType: The created InterventionType model instance.
        """

        obj, created = cls.objects.get_or_create(uuid=ddict["uuid"], defaults=ddict)
        if not created:
            for key, value in ddict.items():
                setattr(obj, key, value)
            obj.save()

        return obj


class Intervention(KnowledgebaseBaseModel):
    types: models.ManyToManyField["InterventionType", "InterventionType"] = (
        models.ManyToManyField(
            "InterventionType",
            related_name="interventions",
            blank=True,
        )
    )

    if TYPE_CHECKING:
        indications: models.Manager["Indication"]
        findings: models.Manager["Finding"]

    @classmethod
    def sync_from_ddict_shallow(
        cls, ddict: InterventionShallowDataDict
    ) -> "Intervention":
        """Create an Intervention model instance from an InterventionShallowDataDict.

        Args:
            ddict (InterventionShallowDataDict): The data dictionary to create the model instance from.
        Returns:
            Intervention: The created Intervention model instance.
        """
        type_names = ddict["type_names"]
        defaults = dict(ddict)
        defaults.pop("type_names", None)

        obj, created = cls.objects.get_or_create(uuid=ddict["uuid"], defaults=defaults)

        if not created:
            for key, value in defaults.items():
                setattr(obj, key, value)

        obj.update_types_by_names(type_names)

        return obj

    @property
    def ddict(self) -> type[InterventionDataDict]:
        return InterventionDataDict

    @property
    def ddict_shallow(self) -> type[InterventionShallowDataDict]:
        return InterventionShallowDataDict

    def to_ddict_shallow(self) -> InterventionShallowDataDict:
        """Convert the Intervention model instance to an InterventionShallowDataDict.

        Returns:
            InterventionShallowDataDict: The converted data dictionary.
        """
        ddict = self._to_ddict()
        type_names = [t.name for t in self.types.all()]
        ddict["type_names"] = type_names
        ddict.pop("types", None)

        ddict = self.ddict_shallow(**ddict)  # type: ignore[assignment]
        return ddict  # type: ignore[return-value]

    def update_types_by_names(
        self,
        type_names: list[str],
    ) -> None:
        """Update the types ManyToManyField based on a list of type names.

        Args:
            type_names (list[str]): A list of type names to associate with this Intervention.
        """
        from .intervention import InterventionType

        types = InterventionType.objects.filter(name__in=type_names)

        retrieved_type_names = [t.name for t in types]
        missing_type_names = set(type_names) - set(retrieved_type_names)
        if missing_type_names:
            raise ValueError(
                f"InterventionType(s) with names {missing_type_names} do not exist."
            )

        self.types.set(types)
        self.save()
