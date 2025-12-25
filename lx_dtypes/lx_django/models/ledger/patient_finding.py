from typing import TYPE_CHECKING, Any, Dict, Self

from django.db import models

from lx_dtypes.models.ledger.patient_finding import (
    PatientFindingDataDict as PfDDict,
)
from lx_dtypes.models.ledger.patient_finding import (
    PatientFindingShallowDataDict as PfShallowDDict,
)

from ..base_model.base_model import LedgerBaseModel
from .utils import transform_kb_name_fields, transform_uuid_fields

if TYPE_CHECKING:
    from lx_dtypes.lx_django.models.core.finding import Finding

    from .patient import Patient
    from .patient_examination import PatientExamination
    from .patient_finding_classifications import PatientFindingClassifications
    from .patient_finding_interventions import PatientFindingInterventions

DDICT = PfDDict
SHALLOW_DDICT = PfShallowDDict


class PatientFinding(LedgerBaseModel):
    class Meta(LedgerBaseModel.Meta):
        pass

    patient_examination: models.ForeignKey[  # TODO Rename to examination?
        "PatientExamination", "PatientExamination"
    ] = models.ForeignKey(
        "PatientExamination",
        on_delete=models.CASCADE,
        related_name="findings",
    )

    finding: models.ForeignKey["Finding", "Finding"] = models.ForeignKey(
        "Finding",
        on_delete=models.CASCADE,
        related_name="patient_findings",
    )

    if TYPE_CHECKING:  # pragma: no cover
        classifications: models.OneToOneField[
            "PatientFindingClassifications", "PatientFindingClassifications"
        ]
        interventions: models.OneToOneField[
            "PatientFindingInterventions", "PatientFindingInterventions"
        ]

    @property
    def ddict(self) -> type[DDICT]:
        return DDICT

    @property
    def ddict_shallow(self) -> type[SHALLOW_DDICT]:
        return SHALLOW_DDICT

    @property
    def patient(self) -> "Patient":
        return self.patient_examination.patient

    @classmethod
    def _ddict_to_defaults(cls, ddict: DDICT) -> Dict[str, Any]:
        defaults = dict(ddict.copy())

        defaults, ledger_instances = transform_uuid_fields(defaults, examination=True)
        defaults, kb_instances = transform_kb_name_fields(
            defaults,
            finding=True,
        )
        defaults["patient_examination"] = ledger_instances.examination
        defaults["finding"] = kb_instances.finding

        return defaults

    @classmethod
    def _remove_nested_ddicts(cls, ddict: Dict[str, Any]) -> Dict[str, Any]:
        ddict_modified = dict(ddict)
        ddict_modified.pop("classifications", None)
        ddict_modified.pop("interventions", None)
        ddict_modified.pop("classifications_uuid", None)
        ddict_modified.pop("interventions_uuid", None)
        return ddict_modified

    @classmethod
    def sync_nested_ddicts(cls, ddict: DDICT) -> None:
        from .patient_finding_classifications import PatientFindingClassifications
        from .patient_finding_interventions import PatientFindingInterventions

        classification_ddict = ddict["classifications"]
        intervention_ddict = ddict["interventions"]

        # Sync classifications
        if classification_ddict:
            PatientFindingClassifications.sync_from_ddict(classification_ddict)

        # Sync interventions
        if intervention_ddict:
            PatientFindingInterventions.sync_from_ddict(intervention_ddict)

    @classmethod
    def sync_from_ddict(cls, ddict: DDICT) -> Self:
        defaults = cls._ddict_to_defaults(ddict)
        defaults = cls._remove_nested_ddicts(defaults)

        instance, created = cls.objects.update_or_create(
            uuid=ddict["uuid"], defaults=defaults
        )

        cls.sync_nested_ddicts(ddict)
        return instance

    def to_ddict_shallow(self) -> SHALLOW_DDICT:
        data_dict = self._to_ddict()

        # pop related fields
        data_dict.pop("patient_examination", None)
        data_dict.pop("finding", None)

        # pop nested fields
        data_dict.pop("classifications", None)
        data_dict.pop("interventions", None)

        data_dict["finding_name"] = self.finding.name
        data_dict["classifications_uuid"] = self.classifications.uuid
        data_dict["interventions_uuid"] = self.interventions.uuid
        data_dict["patient_uuid"] = str(self.patient.uuid)
        data_dict["uuid"] = str(self.uuid)
        data_dict["patient_examination_uuid"] = str(self.patient_examination.uuid)

        ddict = self.ddict_shallow(**data_dict)
        return ddict
