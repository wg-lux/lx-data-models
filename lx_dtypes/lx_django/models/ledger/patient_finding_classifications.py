from typing import TYPE_CHECKING, Any, Dict, Self

from django.db import models

from lx_dtypes.models.ledger.patient_finding_classifications import (
    PatientFindingClassificationsDataDict as PfcDDict,
)
from lx_dtypes.models.ledger.patient_finding_classifications import (
    PatientFindingClassificationsShallowDataDict as PfcShallowDDict,
)

from ..base_model.base_model import LedgerBaseModel
from .utils import transform_kb_name_fields, transform_uuid_fields

if TYPE_CHECKING:
    from .patient import Patient
    from .patient_examination import PatientExamination
    from .patient_finding import PatientFinding
    from .patient_finding_classification_choice import (
        PatientFindingClassificationChoice,
    )

DDICT = PfcDDict
SHALLOW_DDICT = PfcShallowDDict


class PatientFindingClassifications(LedgerBaseModel):
    finding: models.OneToOneField["PatientFinding", "PatientFinding"] = (
        models.OneToOneField(
            "PatientFinding",
            on_delete=models.CASCADE,
            related_name="classifications",
        )
    )

    class Meta(LedgerBaseModel.Meta):
        pass

    @property
    def patient_examination(self) -> "PatientExamination":
        return self.finding.patient_examination

    @property
    def patient(self) -> "Patient":
        return self.patient_examination.patient

    @property
    def ddict(self) -> type[DDICT]:
        return DDICT

    @property
    def ddict_shallow(self) -> type[SHALLOW_DDICT]:
        return SHALLOW_DDICT

    if TYPE_CHECKING:  # pragma: no cover
        choices: models.QuerySet["PatientFindingClassificationChoice"]

    @classmethod
    def _ddict_to_defaults(cls, ddict: DDICT) -> Dict[str, Any]:
        defaults = dict(ddict)

        defaults, ledger_instances = transform_uuid_fields(defaults, finding=True)
        defaults, kb_instances = transform_kb_name_fields(
            defaults,
        )
        defaults["finding"] = ledger_instances.finding

        return defaults

    @classmethod
    def _remove_nested_ddicts(cls, ddict: Dict[str, Any]) -> Dict[str, Any]:
        defaults = dict(ddict)
        defaults.pop("choices", None)
        defaults.pop("choice_uuids", None)
        return defaults

    @classmethod
    def sync_nested_ddicts(cls, ddict: DDICT) -> None:
        from .patient_finding_classification_choice import (
            PatientFindingClassificationChoice,
        )

        choices_ddicts = ddict["choices"]
        for choice_ddict in choices_ddicts:
            PatientFindingClassificationChoice.sync_from_ddict(choice_ddict)

    @classmethod
    def sync_from_ddict(cls, ddict: DDICT) -> Self:
        defaults = cls._ddict_to_defaults(ddict)
        defaults = cls._remove_nested_ddicts(defaults)

        instance, created = cls.objects.update_or_create(
            uuid=ddict["uuid"], defaults=defaults
        )

        cls.sync_nested_ddicts(ddict)
        instance.refresh_from_db()

        return instance

    def to_ddict_shallow(self) -> SHALLOW_DDICT:
        data_dict = self._to_ddict()

        data_dict.pop("finding", None)
        data_dict.pop("choices", None)

        data_dict["uuid"] = str(self.uuid)
        data_dict["choice_uuids"] = [str(choice.uuid) for choice in self.choices.all()]

        data_dict["finding_name"] = self.finding.finding.name
        data_dict["patient_finding_uuid"] = str(self.finding.uuid)
        data_dict["patient_examination_uuid"] = str(
            self.finding.patient_examination.uuid
        )
        data_dict["patient_uuid"] = str(self.patient.uuid)

        ddict = self.ddict_shallow(**data_dict)
        return ddict
