from typing import TYPE_CHECKING, Self

from django.db import models

from lx_dtypes.models.core.finding import FindingDataDict, FindingTypeDataDict
from lx_dtypes.models.core.finding_shallow import (
    FindingShallowDataDict,
    FindingTypeShallowDataDict,
)

from ..base_model.base_model import KnowledgeBaseModel

if TYPE_CHECKING:
    from .classification import Classification
    from .examination import Examination
    from .intervention import Intervention


class FindingType(KnowledgeBaseModel):
    if TYPE_CHECKING:
        findings: models.Manager["Finding"]

    @property
    def ddict(self) -> type[FindingTypeDataDict]:
        return FindingTypeDataDict

    @property
    def ddict_shallow(self) -> type[FindingTypeShallowDataDict]:
        return FindingTypeShallowDataDict

    @classmethod
    def sync_from_ddict_shallow(cls, ddict: FindingTypeShallowDataDict) -> Self:
        """Create a FindingType model instance from a FindingTypeShallowDataDict.
        Args:
            ddict (FindingTypeShallowDataDict): The data dictionary to create the model instance from.
        Returns:
            FindingType: The created FindingType model instance.
        """
        obj, created = cls.objects.get_or_create(uuid=ddict["uuid"], defaults=ddict)
        if not created:
            for key, value in ddict.items():
                setattr(obj, key, value)
            obj.save()
        return obj


class Finding(KnowledgeBaseModel):
    classifications: models.ManyToManyField["Classification", "Classification"] = (
        models.ManyToManyField(
            "Classification",
            related_name="findings",
            blank=True,
        )
    )
    types: models.ManyToManyField["FindingType", "FindingType"] = (
        models.ManyToManyField(
            "FindingType",
            related_name="findings",
            blank=True,
        )
    )

    interventions: models.ManyToManyField["Intervention", "Intervention"] = (
        models.ManyToManyField(
            "Intervention",
            related_name="findings",
            blank=True,
        )
    )

    if TYPE_CHECKING:
        examinations: models.Manager["Examination"]

    @property
    def ddict_shallow(self) -> type[FindingShallowDataDict]:
        return FindingShallowDataDict

    @property
    def ddict(self) -> type[FindingDataDict]:
        return FindingDataDict

    @classmethod
    def sync_from_ddict_shallow(cls, ddict: FindingShallowDataDict) -> Self:
        """Create a Finding model instance from a FindingShallowDataDict.

        Args:
            ddict (FindingShallowDataDict): The data dictionary to create the model instance from.
        Returns:
            Finding: The created Finding model instance.
        """
        t_names = ddict["type_names"]
        c_names = ddict["classification_names"]
        i_names = ddict["intervention_names"]

        defaults = dict(ddict)

        defaults.pop("type_names", None)
        defaults.pop("classification_names", None)
        defaults.pop("intervention_names", None)
        obj, created = cls.objects.get_or_create(uuid=ddict["uuid"], defaults=defaults)
        if not created:
            for key, value in defaults.items():
                setattr(obj, key, value)

        obj.update_types_by_names(t_names)
        obj.update_classifications_by_names(c_names)
        obj.update_interventions_by_names(i_names)

        return obj

    def update_classifications_by_names(self, classification_names: list[str]) -> None:
        """Update the classifications of the Finding model instance based on classification names.

        Args:
            classification_names (list[str]): List of classification names to associate with the Finding.
        """
        from .classification import Classification

        classifications = Classification.objects.filter(name__in=classification_names)
        retrieved_names = [c.name for c in classifications]
        missing_names = set(classification_names) - set(retrieved_names)
        if missing_names:
            raise ValueError(
                f"Classifications with names {missing_names} do not exist."
            )
        self.classifications.set(classifications)
        self.save()

    def update_types_by_names(self, type_names: list[str]) -> None:
        """Update the types of the Finding model instance based on type names.

        Args:
            type_names (list[str]): List of finding type names to associate with the Finding.
        """
        from .finding import FindingType

        types = FindingType.objects.filter(name__in=type_names)
        retrieved_names = [t.name for t in types]
        missing_names = set(type_names) - set(retrieved_names)
        if missing_names:
            raise ValueError(f"FindingTypes with names {missing_names} do not exist.")
        self.types.set(types)
        self.save()

    def update_interventions_by_names(self, intervention_names: list[str]) -> None:
        """Update the interventions of the Finding model instance based on intervention names.

        Args:
            intervention_names (list[str]): List of intervention names to associate with the Finding.
        """
        from .intervention import Intervention

        interventions = Intervention.objects.filter(name__in=intervention_names)
        retrieved_names = [i.name for i in interventions]
        missing_names = set(intervention_names) - set(retrieved_names)
        if missing_names:
            raise ValueError(f"Interventions with names {missing_names} do not exist.")
        self.interventions.set(interventions)
        self.save()

    def to_ddict_shallow(self) -> FindingShallowDataDict:
        """Convert the Finding model instance to a FindingShallowDataDict.

        Returns:
            FindingShallowDataDict: The converted data dictionary.
        """
        ddict = self._to_ddict()

        ddict.pop("classifications", None)
        ddict.pop("types", None)
        ddict.pop("interventions", None)

        ddict["classification_names"] = [c.name for c in self.classifications.all()]
        ddict["type_names"] = [t.name for t in self.types.all()]
        ddict["intervention_names"] = [i.name for i in self.interventions.all()]

        ddict = self.ddict_shallow(**ddict)  # type: ignore[assignment]
        return ddict  # type: ignore[return-value]
