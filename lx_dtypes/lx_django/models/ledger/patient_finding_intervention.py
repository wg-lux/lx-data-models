from typing import TYPE_CHECKING, Any, Dict, Self

from django.db import models

from lx_dtypes.models.ledger.patient_finding_interventions import (
    PatientFindingInterventionDataDict as PfiDDict,
)
from lx_dtypes.models.ledger.patient_finding_interventions import (
    PatientFindingInterventionShallowDataDict as PfiShallowDDict,
)

from ..base_model.base_model import LedgerBaseModel
from .utils import transform_kb_name_fields, transform_uuid_fields

if TYPE_CHECKING:
    from lx_dtypes.lx_django.models.core.intervention import Intervention

    from .patient import Patient
    from .patient_examination import PatientExamination
    from .patient_finding import PatientFinding
    from .patient_finding_interventions import PatientFindingInterventions

DDICT = PfiDDict
SHALLOW_DDICT = PfiShallowDDict


class PatientFindingIntervention(LedgerBaseModel):
    parent: models.ForeignKey[
        "PatientFindingInterventions", "PatientFindingInterventions"
    ] = models.ForeignKey(
        "PatientFindingInterventions",
        on_delete=models.CASCADE,
        related_name="interventions",
    )
    intervention: models.ForeignKey["Intervention", "Intervention"] = models.ForeignKey(
        "Intervention",
        on_delete=models.CASCADE,
        related_name="patient_finding_interventions",
    )

    class Meta(LedgerBaseModel.Meta):
        pass

    @property
    def ddict(self) -> type[DDICT]:
        return DDICT

    @property
    def ddict_shallow(self) -> type[SHALLOW_DDICT]:
        return SHALLOW_DDICT

    @property
    def patient_finding(self) -> "PatientFinding":
        return self.parent.finding

    @property
    def patient_examination(self) -> "PatientExamination":
        return self.patient_finding.patient_examination

    if TYPE_CHECKING:  # pragma: no cover
        interventions: models.QuerySet["PatientFindingIntervention"]

    @property
    def patient(self) -> "Patient":
        return self.patient_examination.patient

    @classmethod
    def _ddict_to_defaults(cls, ddict: DDICT) -> Dict[str, Any]:
        defaults = dict(ddict)

        defaults, ledger_instances = transform_uuid_fields(defaults, interventions=True)
        defaults, kb_instances = transform_kb_name_fields(defaults, intervention=True)
        defaults["parent"] = ledger_instances.interventions
        defaults["intervention"] = kb_instances.intervention

        return defaults

    @classmethod
    def _remove_nested_ddicts(cls, ddict: Dict[str, Any]) -> Dict[str, Any]:
        return dict(ddict)  # No nested ddicts to remove

    @classmethod
    def _remove_related_ddicts(cls, ddict: Dict[str, Any]) -> Dict[str, Any]:
        defaults = dict(ddict)
        defaults.pop("parent", None)
        defaults.pop("intervention", None)
        return defaults

    @classmethod
    def sync_nested_ddicts(cls, ddict: DDICT) -> None:
        pass  # No nested ddicts to sync

    @classmethod
    def sync_from_ddict(cls, ddict: DDICT) -> Self:
        defaults = cls._ddict_to_defaults(ddict)
        defaults = cls._remove_nested_ddicts(defaults)
        defaults = cls._remove_related_ddicts(defaults)

        instance, _ = cls.objects.update_or_create(
            uuid=ddict["uuid"],
            defaults=defaults,
        )

        cls.sync_nested_ddicts(ddict)

        instance.refresh_from_db()
        return instance
