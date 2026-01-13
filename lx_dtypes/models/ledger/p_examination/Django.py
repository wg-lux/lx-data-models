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


class PExaminationDjango(LedgerBaseModelDjango[PExaminationDataDict]):
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

    @property
    def ddict_class(self) -> type[PExaminationDataDict]:
        return PExaminationDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return P_EXAMINATION_MODEL_LIST_TYPE_FIELDS

    @classmethod
    def nested_fields(cls) -> list[str]:
        return P_EXAMINATION_MODEL_NESTED_FIELDS

    class Meta(LedgerBaseModelDjango.Meta):
        abstract = False
