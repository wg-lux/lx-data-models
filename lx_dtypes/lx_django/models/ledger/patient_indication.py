from typing import TYPE_CHECKING, Any, Dict, Self

from django.db import models

from lx_dtypes.models.ledger.patient_indication import (
    PatientIndicationDataDict as PiDDict,
)
from lx_dtypes.models.ledger.patient_indication import (
    PatientIndicationShallowDataDict as PiShallowDDict,
)

from ..base_model.base_model import LedgerBaseModel
from .utils import transform_kb_name_fields, transform_uuid_fields

if TYPE_CHECKING:
    from lx_dtypes.lx_django.models.core.indication import Indication

    from .patient import Patient
    from .patient_examination import PatientExamination

DDICT = PiDDict
SHALLOW_DDICT = PiShallowDDict


class PatientIndication(LedgerBaseModel):
    patient_examination: models.ForeignKey[
        "PatientExamination", "PatientExamination"
    ] = models.ForeignKey(
        "PatientExamination",
        on_delete=models.CASCADE,
        related_name="indications",
    )
    indication: models.ForeignKey["Indication", "Indication"] = models.ForeignKey(
        "Indication",
        on_delete=models.CASCADE,
        related_name="patient_indications",
    )

    class Meta(LedgerBaseModel.Meta):
        pass

    @property
    def ddict(self) -> type[DDICT]:
        return DDICT

    @property
    def ddict_shallow(self) -> type[SHALLOW_DDICT]:
        return SHALLOW_DDICT

    if TYPE_CHECKING:  # pragma: no cover
        pass

    @classmethod
    def _ddict_to_defaults(cls, ddict: DDICT) -> Dict[str, Any]:
        defaults = dict(ddict)
        defaults, ledger_instances = transform_uuid_fields(defaults, examination=True)
        defaults, kb_instances = transform_kb_name_fields(
            defaults,
            indication=True,
        )
        defaults["patient_examination"] = ledger_instances.examination
        defaults["indication"] = kb_instances.indication
        return defaults

    @property
    def patient(self) -> "Patient":
        return self.patient_examination.patient

    @classmethod
    def sync_from_ddict(cls, ddict: DDICT) -> Self:
        defaults = cls._ddict_to_defaults(ddict)
        instance, _created = cls.objects.update_or_create(
            uuid=ddict["uuid"],
            defaults=defaults,
        )
        return instance
