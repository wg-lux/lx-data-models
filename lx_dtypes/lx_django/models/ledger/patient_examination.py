from typing import TYPE_CHECKING, Any, Dict, Self

from django.db import models

from lx_dtypes.models.ledger.patient_examination import (
    PatientExaminationDataDict as PeDDict,
)
from lx_dtypes.models.ledger.patient_examination import (
    PatientExaminationShallowDataDict as PeShallowDDict,
)

from ..base_model.base_model import LedgerBaseModel
from ..typing import OptionalDateTimeField
from .utils import transform_kb_name_fields, transform_uuid_fields

if TYPE_CHECKING:
    from ..core.examination import Examination
    from .patient import Patient
    from .patient_finding import PatientFinding
    from .patient_indication import PatientIndication


DDICT = PeDDict
SHALLOW_DDICT = PeShallowDDict


class PatientExamination(LedgerBaseModel):
    patient: models.ForeignKey["Patient", "Patient"] = models.ForeignKey(
        "Patient",
        on_delete=models.CASCADE,
        related_name="examinations",
    )
    examination: models.ForeignKey["Examination", "Examination"] = models.ForeignKey(
        "Examination",
        on_delete=models.CASCADE,
        related_name="patient_examinations",
    )
    date: OptionalDateTimeField = models.DateTimeField(null=True, blank=True)

    if TYPE_CHECKING:  # pragma: no cover
        findings: models.QuerySet["PatientFinding"]
        indications: models.QuerySet["PatientIndication"]

    class Meta(LedgerBaseModel.Meta):
        pass

    @property
    def ddict(self) -> type[DDICT]:
        return DDICT

    @property
    def ddict_shallow(self) -> type[SHALLOW_DDICT]:
        return SHALLOW_DDICT

    @classmethod
    def _ddict_to_defaults(cls, ddict: DDICT) -> Dict[str, Any]:
        defaults = dict(ddict)
        defaults, ledger_instances = transform_uuid_fields(
            defaults, patient=True, indications=True
        )
        defaults, kb_instances = transform_kb_name_fields(
            defaults,
            examination=True,
        )
        defaults["patient"] = ledger_instances.patient
        defaults["examination"] = kb_instances.examination

        return defaults

    @classmethod
    def _remove_nested_ddicts(cls, ddict: Dict[str, Any]) -> Dict[str, Any]:
        defaults = dict(ddict)
        defaults.pop("patient_findings", None)
        defaults.pop("patient_indications", None)
        return defaults

    @classmethod
    def _remove_related_ddicts(cls, ddict: Dict[str, Any]) -> Dict[str, Any]:
        defaults = dict(ddict)
        defaults.pop("patient", None)
        defaults.pop("examination", None)
        return defaults

    @classmethod
    def sync_nested_ddicts(cls, ddict: DDICT) -> None:
        from .patient_finding import PatientFinding
        from .patient_indication import PatientIndication

        finding_ddicts = ddict["patient_findings"]
        for finding_ddict in finding_ddicts:
            PatientFinding.sync_from_ddict(finding_ddict)

        indication_ddicts = ddict["patient_indications"]
        for indication_ddict in indication_ddicts:
            PatientIndication.sync_from_ddict(indication_ddict)

    @classmethod
    def sync_from_ddict(
        cls,
        ddict: DDICT,
    ) -> Self:
        defaults = cls._ddict_to_defaults(ddict)
        defaults = cls._remove_nested_ddicts(defaults)
        # defaults = cls._remove_related_ddicts(defaults)

        # TODO
        defaults.pop("examination_template", None)

        obj, updated = cls.objects.update_or_create(
            uuid=ddict["uuid"], defaults=defaults
        )
        cls.sync_nested_ddicts(ddict)
        obj.refresh_from_db()
        return obj

    def to_ddict_shallow(self) -> SHALLOW_DDICT:
        from lx_dtypes.models.ledger.patient_examination import (
            PatientExaminationShallowDataDict,
        )

        data_dict = self._to_ddict()

        data_dict.pop("patient", None)
        patient_uuid = str(self.patient.uuid)
        examination_name = self.examination.name
        patient_findings_uuids = [str(finding.uuid) for finding in self.findings]
        patient_indications_uuids = [
            str(indication.uuid) for indication in self.indications
        ]
        date = self.date.isoformat() if self.date else None

        ddict = PatientExaminationShallowDataDict(
            uuid=str(self.uuid),
            patient_uuid=patient_uuid,
            examination_name=examination_name,
            examination_template=None,  # TODO
            date=date,
            patient_findings_uuids=patient_findings_uuids,
            patient_indications_uuids=patient_indications_uuids,
            tags=[],  # TODO
        )

        return ddict


#     def to_ddict_shallow(self) -> SHALLOW_DDICT:
#         """Convert the Center model instance to a CenterShallowDataDict.

#         Returns:
#             CenterShallowDataDict: The converted data dictionary.
#         """
#         data_dict = self._to_ddict()
#         # TODO handle uuids of related examination, patient, ....
#         ddict = self.ddict_shallow(**data_dict)
#         return ddict
