from typing import TYPE_CHECKING, Any, Dict, Self

from django.db import models

from lx_dtypes.models.ledger.patient_finding_classification_choice import (
    PatientFindingClassificationChoiceDataDict as PfccDDict,
)
from lx_dtypes.models.ledger.patient_finding_classification_choice import (
    PatientFindingClassificationChoiceShallowDataDict as PfccShallowDDict,
)

from ..base_model.base_model import LedgerBaseModel
from .utils import transform_kb_name_fields, transform_uuid_fields

if TYPE_CHECKING:
    from lx_dtypes.lx_django.models.core.classification import Classification
    from lx_dtypes.lx_django.models.core.classification_choice import (
        ClassificationChoice,
    )

    from .patient import Patient
    from .patient_examination import PatientExamination
    from .patient_finding import PatientFinding
    from .patient_finding_classification_choice_descriptor import (
        PatientFindingClassificationChoiceDescriptor,
    )
    from .patient_finding_classifications import PatientFindingClassifications

DDICT = PfccDDict
SHALLOW_DDICT = PfccShallowDDict


class PatientFindingClassificationChoice(LedgerBaseModel):
    parent: models.ForeignKey[
        "PatientFindingClassifications", "PatientFindingClassifications"
    ] = models.ForeignKey(
        "PatientFindingClassifications",
        on_delete=models.CASCADE,
        related_name="choices",
    )
    classification: models.ForeignKey["Classification", "Classification"] = (
        models.ForeignKey(
            "Classification",
            on_delete=models.CASCADE,
            related_name="patient_finding_classification_choices",
        )
    )
    choice: models.ForeignKey["ClassificationChoice", "ClassificationChoice"] = (
        models.ForeignKey(
            "ClassificationChoice",
            on_delete=models.CASCADE,
            related_name="patient_finding_classification_choices",
        )
    )
    if TYPE_CHECKING:  # pragma: no cover
        descriptors: models.QuerySet["PatientFindingClassificationChoiceDescriptor"]

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

    @property
    def patient(self) -> "Patient":
        return self.patient_examination.patient

    @classmethod
    def _ddict_to_defaults(cls, ddict: DDICT) -> Dict[str, Any]:
        defaults = dict(ddict)
        defaults, ledger_instances = transform_uuid_fields(
            defaults, classifications=True
        )
        defaults, kb_instances = transform_kb_name_fields(
            defaults, classification_choice=True, classification=True
        )
        defaults["parent"] = ledger_instances.classifications
        defaults["classification"] = kb_instances.classification
        defaults["choice"] = kb_instances.classification_choice

        return defaults

    @classmethod
    def _remove_nested_ddicts(cls, ddict: Dict[str, Any]) -> Dict[str, Any]:
        defaults = dict(ddict)
        defaults.pop("descriptors", None)
        defaults.pop("descriptor_uuids", None)
        return defaults

    @classmethod
    def _remove_related_ddicts(cls, ddict: Dict[str, Any]) -> Dict[str, Any]:
        defaults = dict(ddict)
        defaults.pop("parent", None)
        defaults.pop("classification", None)
        defaults.pop("choice", None)

        return defaults

    @classmethod
    def sync_nested_ddicts(cls, ddict: DDICT) -> None:
        from .patient_finding_classification_choice_descriptor import (
            PatientFindingClassificationChoiceDescriptor,
        )

        descriptors_ddicts = ddict["descriptors"]
        for descriptor_ddict in descriptors_ddicts:
            PatientFindingClassificationChoiceDescriptor.sync_from_ddict(
                descriptor_ddict
            )

    @classmethod
    def sync_from_ddict(
        cls,
        ddict: DDICT,
    ) -> Self:
        defaults = cls._ddict_to_defaults(ddict)
        defaults = cls._remove_nested_ddicts(defaults)
        # defaults = cls._remove_related_ddicts(defaults)

        obj, _updated = cls.objects.update_or_create(
            uuid=ddict["uuid"], defaults=defaults
        )

        cls.sync_nested_ddicts(ddict)

        return obj

    def to_ddict_shallow(self) -> SHALLOW_DDICT:
        data_dict = self._to_ddict()

        data_dict = self._remove_related_ddicts(data_dict)
        data_dict = self._remove_nested_ddicts(data_dict)

        data_dict["choice_name"] = self.choice.name
        data_dict["classification_name"] = self.classification.name

        data_dict["uuid"] = str(self.uuid)
        data_dict["patient_uuid"] = str(self.patient.uuid)
        data_dict["patient_finding_classifications_uuid"] = str(self.parent.uuid)
        data_dict["patient_finding_uuid"] = str(self.patient_finding.uuid)
        data_dict["patient_examination_uuid"] = str(
            self.parent.finding.patient_examination.uuid
        )
        descriptor_uuids = [
            str(descriptor.uuid) for descriptor in self.descriptors.all()
        ]

        data_dict["descriptor_uuids"] = descriptor_uuids

        ddict = self.ddict_shallow(**data_dict)
        return ddict
