from typing import TYPE_CHECKING, Self

from django.db import models

from lx_dtypes.models.core.indication import (
    IndicationDataDict,
    IndicationTypeDataDict,
)
from lx_dtypes.models.core.indication_shallow import (
    IndicationShallowDataDict,
    IndicationTypeShallowDataDict,
)

from ..base_model.base_model import KnowledgebaseBaseModel

if TYPE_CHECKING:
    from ..ledger.patient_indication import PatientIndication
    from .examination import Examination
    from .intervention import Intervention


class IndicationType(KnowledgebaseBaseModel):
    if TYPE_CHECKING:
        indications: models.Manager["Indication"]

    @property
    def ddict_shallow(self) -> type[IndicationTypeShallowDataDict]:
        return IndicationTypeShallowDataDict

    @property
    def ddict(self) -> type[IndicationTypeDataDict]:
        return IndicationTypeDataDict

    @classmethod
    def sync_from_ddict_shallow(
        cls, ddict: IndicationTypeShallowDataDict
    ) -> "IndicationType":
        """Create an IndicationType model instance from an IndicationTypeShallowDataDict.

        Args:
            ddict (IndicationTypeShallowDataDict): The data dictionary to create the model instance from.
        Returns:
            IndicationType: The created IndicationType model instance.
        """

        obj, created = cls.objects.get_or_create(uuid=ddict["uuid"], defaults=ddict)
        if not created:
            for key, value in ddict.items():
                setattr(obj, key, value)
            obj.save()

        return obj


class Indication(KnowledgebaseBaseModel):
    expected_interventions: models.ManyToManyField["Intervention", "Intervention"] = (
        models.ManyToManyField(
            "Intervention",
            related_name="indications",
            blank=True,
        )
    )

    types: models.ManyToManyField["IndicationType", "IndicationType"] = (
        models.ManyToManyField(
            IndicationType,
            related_name="indications",
            blank=True,
        )
    )

    if TYPE_CHECKING:
        examinations: models.Manager["Examination"]
        patient_indications: models.Manager["PatientIndication"]

    @classmethod
    def sync_from_ddict_shallow(cls, ddict: IndicationShallowDataDict) -> Self:
        """Create an Indication model instance from an IndicationShallowDataDict.

        Args:
            ddict (IndicationShallowDataDict): The data dictionary to create the model instance from.
        Returns:
            Indication: The created Indication model instance.
        """
        intervention_names = ddict["expected_intervention_names"]
        type_names = ddict["type_names"]
        defaults = dict(ddict)
        defaults.pop("expected_intervention_names", None)
        defaults.pop("type_names", None)

        obj, created = cls.objects.get_or_create(uuid=ddict["uuid"], defaults=defaults)
        if not created:
            for key, value in defaults.items():
                setattr(obj, key, value)

        obj.update_expected_interventions_by_names(intervention_names)
        obj.update_types_by_names(type_names)

        return obj

    @property
    def ddict_shallow(self) -> type[IndicationShallowDataDict]:
        return IndicationShallowDataDict

    @property
    def ddict(self) -> type[IndicationDataDict]:
        return IndicationDataDict

    def update_types_by_names(self, type_names: list[str]) -> None:
        """Update the IndicationType relationships based on a list of type names.

        Args:
            type_names (list[str]): A list of IndicationType names to associate with this Indication.
        """

        types = IndicationType.objects.filter(name__in=type_names)
        retrieved_names = {t.name for t in types}
        missing_names = set(type_names) - retrieved_names
        if missing_names:
            raise ValueError(
                f"IndicationTypes with names {missing_names} do not exist."
            )
        self.types.set(types)
        self.save()

    def update_expected_interventions_by_names(
        self,
        intervention_names: list[str],
    ) -> None:
        """Update the expected_interventions ManyToManyField based on a list of intervention names.

        Args:
            intervention_names (list[str]): A list of intervention names to associate with this Indication.
        """
        from .intervention import Intervention

        interventions = Intervention.objects.filter(name__in=intervention_names)

        retrieved_names = {i.name for i in interventions}
        missing_names = set(intervention_names) - retrieved_names
        if missing_names:
            raise ValueError(f"Interventions with names {missing_names} do not exist.")

        self.expected_interventions.set(interventions)
        self.save()

    def to_ddict_shallow(self) -> IndicationShallowDataDict:
        """Convert the Indication model instance to a IndicationShallowDataDict.

        Returns:
            IndicationShallowDataDict: The converted data dictionary.
        """
        ddict = self._to_ddict()
        ddict.pop("expected_interventions", None)
        ddict.pop("types", None)

        ddict["expected_intervention_names"] = [
            i.name for i in self.expected_interventions.all()
        ]
        ddict["type_names"] = [t.name for t in self.types.all()]

        ddict = self.ddict_shallow(**ddict)  # type: ignore[assignment]
        return ddict  # type: ignore[return-value]
