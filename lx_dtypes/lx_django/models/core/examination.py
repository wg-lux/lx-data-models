from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

from lx_dtypes.models.core.examination import (
    ExaminationDataDict,
    ExaminationTypeDataDict,
)
from lx_dtypes.models.core.examination_shallow import (
    ExaminationShallowDataDict,
    ExaminationTypeShallowDataDict,
)

from ..base_model.base_model import KnowledgebaseBaseModel

if TYPE_CHECKING:
    from ..ledger.patient_examination import PatientExamination
    from .finding import Finding
    from .indication import Indication


class ExaminationType(KnowledgebaseBaseModel):
    if TYPE_CHECKING:
        examinations: models.Manager["Examination"]
        patient_examinations: models.QuerySet["PatientExamination"]

    @property
    def ddict_shallow(self) -> type[ExaminationTypeShallowDataDict]:
        return ExaminationTypeShallowDataDict

    @property
    def ddict(self) -> type[ExaminationTypeDataDict]:
        return ExaminationTypeDataDict

    @classmethod
    def sync_from_ddict_shallow(
        cls, ddict: ExaminationTypeShallowDataDict
    ) -> "ExaminationType":
        """Create an ExaminationType model instance from an ExaminationTypeShallowDataDict.

        Args:
            ddict (ExaminationTypeShallowDataDict): The data dictionary to create the model instance from.
        Returns:
            ExaminationType: The created ExaminationType model instance.
        """

        obj, created = cls.objects.get_or_create(uuid=ddict["uuid"], defaults=ddict)
        if not created:
            for key, value in ddict.items():
                setattr(obj, key, value)
            obj.save()

        return obj


class Examination(KnowledgebaseBaseModel):
    findings: models.ManyToManyField["Finding", "Finding"] = models.ManyToManyField(
        "Finding",
        related_name="examinations",
        blank=True,
    )

    types: models.ManyToManyField["ExaminationType", "ExaminationType"] = (
        models.ManyToManyField(
            ExaminationType,
            related_name="examinations",
            blank=True,
        )
    )

    indications: models.ManyToManyField["Indication", "Indication"] = (
        models.ManyToManyField(
            "Indication",
            related_name="examinations",
            blank=True,
        )
    )

    @classmethod
    def sync_from_ddict_shallow(
        cls, ddict: ExaminationShallowDataDict
    ) -> "Examination":
        """Create an Examination model instance from an ExaminationShallowDataDict.

        Args:
            ddict (ExaminationShallowDataDict): The data dictionary to create the model instance from.
        Returns:
            Examination: The created Examination model instance.
        """
        indication_names = ddict["indication_names"]
        type_names = ddict["type_names"]
        finding_names = ddict["finding_names"]

        defaults = dict(ddict)

        defaults.pop("indication_names", None)
        defaults.pop("type_names", None)
        defaults.pop("finding_names", None)
        obj, created = cls.objects.get_or_create(uuid=ddict["uuid"], defaults=defaults)

        if not created:
            for key, value in defaults.items():
                setattr(obj, key, value)

        obj.update_indications_by_names(indication_names)
        obj.update_types_by_names(type_names)
        obj.update_findings_by_names(finding_names)

        return obj

    @property
    def ddict_shallow(self) -> type[ExaminationShallowDataDict]:
        return ExaminationShallowDataDict

    @property
    def ddict(self) -> type[ExaminationDataDict]:
        return ExaminationDataDict

    def update_findings_by_names(self, finding_names: list[str]) -> None:
        from .finding import Finding

        findings = Finding.objects.filter(name__in=finding_names)

        retrieved_names = set(f.name for f in findings)
        missing_names = set(finding_names) - retrieved_names
        if missing_names:
            raise ValueError(f"Findings with names {missing_names} do not exist.")
        self.findings.set(findings)
        self.save()

    def update_types_by_names(self, type_names: list[str]) -> None:
        from .examination import ExaminationType

        types = ExaminationType.objects.filter(name__in=type_names)

        retrieved_names = set(t.name for t in types)
        missing_names = set(type_names) - retrieved_names
        if missing_names:
            raise ValueError(
                f"ExaminationTypes with names {missing_names} do not exist."
            )
        self.types.set(types)
        self.save()

    def update_indications_by_names(self, indication_names: list[str]) -> None:
        from .indication import Indication

        indications = Indication.objects.filter(name__in=indication_names)

        retrieved_names = set(i.name for i in indications)
        missing_names = set(indication_names) - retrieved_names
        if missing_names:
            raise ValueError(f"Indications with names {missing_names} do not exist.")
        self.indications.set(indications)
        self.save()

    def to_ddict_shallow(self) -> ExaminationShallowDataDict:
        """Convert the Examination model instance to a ExaminationShallowDataDict.

        Returns:
            ExaminationShallowDataDict: The converted data dictionary.
        """
        ddict = self._to_ddict()

        ddict.pop("findings", None)
        ddict.pop("types", None)
        ddict.pop("indications", None)

        f_names = [f.name for f in self.findings.all()]
        t_names = [t.name for t in self.types.all()]
        i_names = [i.name for i in self.indications.all()]

        ddict["finding_names"] = f_names
        ddict["type_names"] = t_names
        ddict["indication_names"] = i_names

        ddict = self.ddict_shallow(**ddict)  # type: ignore[assignment]
        return ddict  # type: ignore[return-value]
