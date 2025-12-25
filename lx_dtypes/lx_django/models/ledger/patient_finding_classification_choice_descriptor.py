from typing import TYPE_CHECKING, Any, Dict, Self

from django.db import models

from lx_dtypes.lx_django.models.typing import CharFieldType
from lx_dtypes.models.ledger.patient_classification_choice_descriptor import (
    PatientFindingClassificationChoiceDescriptorDataDict as PfccdDDict,
)
from lx_dtypes.models.ledger.patient_classification_choice_descriptor import (
    PatientFindingClassificationChoiceDescriptorShallowDataDict as PfccdShallowDDict,
)

from ..base_model.base_model import LedgerBaseModel
from .utils import transform_kb_name_fields, transform_uuid_fields

if TYPE_CHECKING:
    from lx_dtypes.lx_django.models.core.classification_choice_descriptor import (
        ClassificationChoiceDescriptor,
    )
    from lx_dtypes.lx_django.models.ledger.patient import Patient
    from lx_dtypes.lx_django.models.ledger.patient_examination import (
        PatientExamination,
    )
    from lx_dtypes.lx_django.models.ledger.patient_finding import (
        PatientFinding,
    )
    from lx_dtypes.lx_django.models.ledger.patient_finding_classification_choice import (
        PatientFindingClassificationChoice,
    )

DDICT = PfccdDDict
SHALLOW_DDICT = PfccdShallowDDict


class PatientFindingClassificationChoiceDescriptor(LedgerBaseModel):
    choice: models.ForeignKey[
        "PatientFindingClassificationChoice", "PatientFindingClassificationChoice"
    ] = models.ForeignKey(
        "PatientFindingClassificationChoice",
        on_delete=models.CASCADE,
        related_name="descriptors",
    )
    descriptor_value: CharFieldType = models.CharField(max_length=255)
    descriptor: models.ForeignKey[
        "ClassificationChoiceDescriptor", "ClassificationChoiceDescriptor"
    ] = models.ForeignKey(
        "ClassificationChoiceDescriptor",
        on_delete=models.CASCADE,
        related_name="patient_finding_classification_choice_descriptors",
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

        defaults, ledger_instances = transform_uuid_fields(
            defaults, classification_choice=True
        )
        defaults, kb_instances = transform_kb_name_fields(
            defaults, classification_choice_descriptor=True
        )

        defaults["choice"] = ledger_instances.classification_choice
        defaults["descriptor"] = kb_instances.classification_choice_descriptor

        return defaults

    @classmethod
    def sync_from_ddict(
        cls,
        ddict: DDICT,
    ) -> Self:
        defaults = cls._ddict_to_defaults(ddict)
        obj, created = cls.objects.get_or_create(uuid=ddict["uuid"], defaults=defaults)
        if not created:
            for key, value in defaults.items():
                setattr(obj, key, value)
            obj.save()

        return obj

    def to_ddict_shallow(self) -> SHALLOW_DDICT:
        """Convert the Center model instance to a CenterShallowDataDict.

        Returns:
            CenterShallowDataDict: The converted data dictionary.
        """
        data_dict = self._to_ddict()
        data_dict["uuid"] = str(self.uuid)
        data_dict["patient_uuid"] = str(self.patient.uuid)
        data_dict["patient_examination_uuid"] = str(self.patient_examination.uuid)
        data_dict["patient_finding_uuid"] = str(self.patient_finding.uuid)
        data_dict["patient_finding_classifications_uuid"] = str(self.choice.parent.uuid)
        data_dict["patient_finding_classification_choice_uuid"] = str(self.choice.uuid)
        data_dict["descriptor_name"] = self.descriptor.name

        data_dict.pop("choice", None)
        data_dict.pop("descriptor", None)

        ddict = self.ddict_shallow(**data_dict)
        return ddict

    @property
    def patient(self) -> "Patient":
        patient_examination = self.patient_examination
        patient = patient_examination.patient
        return patient

    @property
    def patient_finding(self) -> "PatientFinding":
        finding = self.choice.parent.finding
        return finding

    @property
    def patient_examination(self) -> "PatientExamination":
        finding = self.patient_finding
        patient_examination = finding.patient_examination
        return patient_examination
