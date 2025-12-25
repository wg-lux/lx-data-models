from typing import TYPE_CHECKING, Any, Dict, Self

from django.db import models

from lx_dtypes.models.ledger.patient_finding_interventions import (
    PatientFindingInterventionsDataDict as PfiDDict,
)
from lx_dtypes.models.ledger.patient_finding_interventions import (
    PatientFindingInterventionsShallowDataDict as PfiShallowDDict,
)

from ..base_model.base_model import LedgerBaseModel
from .utils import transform_kb_name_fields, transform_uuid_fields

if TYPE_CHECKING:
    from .patient import Patient as DjPatient
    from .patient_examination import PatientExamination as DjPatientExamination
    from .patient_finding import PatientFinding as DjPatientFinding
    from .patient_finding_intervention import (
        PatientFindingIntervention as DjPatientFindingIntervention,
    )

DDICT = PfiDDict
SHALLOW_DDICT = PfiShallowDDict


class PatientFindingInterventions(LedgerBaseModel):
    finding: models.OneToOneField["DjPatientFinding", "DjPatientFinding"] = (
        models.OneToOneField(
            "PatientFinding",
            on_delete=models.CASCADE,
            related_name="interventions",
        )
    )

    class Meta(LedgerBaseModel.Meta):
        pass

    if TYPE_CHECKING:  # pragma: no cover
        interventions: models.QuerySet["DjPatientFindingIntervention"]

    @property
    def ddict(self) -> type[DDICT]:
        return DDICT

    @property
    def ddict_shallow(self) -> type[SHALLOW_DDICT]:
        return SHALLOW_DDICT

    @property
    def patient_examination(self) -> "DjPatientExamination":
        return self.finding.patient_examination

    @property
    def patient(self) -> "DjPatient":
        return self.patient_examination.patient

    @classmethod
    def _ddict_to_defaults(cls, ddict: DDICT) -> Dict[str, Any]:
        defaults = dict(ddict)

        defaults, ledger_instances = transform_uuid_fields(defaults, finding=True)
        defaults, kb_instances = transform_kb_name_fields(
            defaults,
        )
        defaults["finding"] = kb_instances.finding

        return defaults

    @classmethod
    def _remove_nested_ddicts(cls, ddict: Dict[str, Any]) -> Dict[str, Any]:
        defaults = dict(ddict)
        defaults.pop("interventions", None)
        return defaults

    @classmethod
    def sync_nested_ddicts(cls, ddict: DDICT) -> None:
        from .patient_finding_intervention import (
            PatientFindingIntervention as DjPatientFindingIntervention,
        )

        interventions_ddicts = ddict["interventions"]
        for intervention_ddict in interventions_ddicts:
            DjPatientFindingIntervention.sync_from_ddict(intervention_ddict)

    @classmethod
    def _remove_related_ddicts(cls, ddict: Dict[str, Any]) -> Dict[str, Any]:
        defaults = dict(ddict)
        defaults.pop("finding", None)
        return defaults

    @classmethod
    def sync_from_ddict(cls, ddict: DDICT) -> Self:
        defaults = cls._ddict_to_defaults(ddict)
        defaults = cls._remove_nested_ddicts(defaults)
        defaults = cls._remove_related_ddicts(defaults)

        instance, _ = cls.objects.update_or_create(
            uuid=ddict["uuid"], defaults=defaults
        )

        cls.sync_nested_ddicts(ddict)

        instance.refresh_from_db()

        return instance
