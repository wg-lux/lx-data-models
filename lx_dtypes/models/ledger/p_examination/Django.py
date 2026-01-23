from typing import TYPE_CHECKING

from django.db import models

from lx_dtypes.models.base.app_base_model.django.LedgerBaseModelDjango import (
    LedgerBaseModelDjango,
)
from lx_dtypes.names import (
    P_EXAMINATION_MODEL_LIST_TYPE_FIELDS,
    P_EXAMINATION_MODEL_NESTED_FIELDS,
    FieldNames,
)
from lx_dtypes.utils.django_field_types import OptionalDateTimeField

from .DataDict import (
    PExaminationDataDict,
)

if TYPE_CHECKING:
    from lx_dtypes.models.knowledge_base.examination.ExaminationDjango import (
        ExaminationDjango,
    )
    from lx_dtypes.models.ledger.examiner.Django import (
        ExaminerDjango,
    )
    from lx_dtypes.models.ledger.p_finding.Django import (
        PFindingDjango,
    )
    from lx_dtypes.models.ledger.p_indication.Django import (
        PIndicationDjango,
    )
    from lx_dtypes.models.ledger.patient.Django import (
        PatientDjango,
    )


class PExaminationDjango(LedgerBaseModelDjango[PExaminationDataDict]):
    patient: models.ForeignKey["PatientDjango", "PatientDjango"] = models.ForeignKey(
        "PatientDjango",
        related_name=FieldNames.PATIENT_EXAMINATIONS.value,
        on_delete=models.CASCADE,
    )
    examiners: models.ManyToManyField["ExaminerDjango", "ExaminerDjango"] = (
        models.ManyToManyField(
            "ExaminerDjango",
            related_name=FieldNames.PATIENT_EXAMINATIONS.value,
        )
    )

    examination: models.ForeignKey["ExaminationDjango", "ExaminationDjango"] = (
        models.ForeignKey(
            "ExaminationDjango",
            related_name=FieldNames.PATIENT_EXAMINATIONS.value,
            on_delete=models.CASCADE,
        )
    )
    date: OptionalDateTimeField = models.DateTimeField(null=True, blank=True)

    if TYPE_CHECKING:
        patient_findings: models.Manager["PFindingDjango"]
        patient_indications: models.Manager["PIndicationDjango"]

    @property
    def ddict_class(self) -> type[PExaminationDataDict]:
        """
        Return the data-dict class associated with this model.

        Returns:
            type[PExaminationDataDict]: The PExaminationDataDict class used for this model's data dictionary representation.
        """
        return PExaminationDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        """
        Return the field names on this model that are treated as list-typed.

        Returns:
            list[str]: Field names that represent list-valued relationships or collections for this model.
        """
        return P_EXAMINATION_MODEL_LIST_TYPE_FIELDS

    @classmethod
    def nested_fields(cls) -> list[str]:
        """
        Return the names of fields that should be treated as nested for this model.

        Returns:
            list[str]: Field names considered nested (to be serialized/deserialized as nested objects).
        """
        return P_EXAMINATION_MODEL_NESTED_FIELDS

    class Meta(LedgerBaseModelDjango.Meta):
        abstract = False
