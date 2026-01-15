from typing import TYPE_CHECKING

from django.db import models

from lx_dtypes.models.base.app_base_model.django.LedgerBaseModelDjango import (
    LedgerBaseModelDjango,
)
from lx_dtypes.models.base.app_base_model.django.PersonDjango import (
    PersonDjango,
)
from lx_dtypes.names import (
    PATIENT_MODEL_LIST_TYPE_FIELDS,
    PATIENT_MODEL_NESTED_FIELDS,
    FieldNames,
)

from .DataDict import (
    PatientDataDict,
)

if TYPE_CHECKING:
    from lx_dtypes.models.ledger.center.Django import (
        CenterDjango,
    )
    from lx_dtypes.models.ledger.p_examination.Django import (
        PExaminationDjango,
    )


class PatientDjango(PersonDjango, LedgerBaseModelDjango[PatientDataDict]):
    center: models.ForeignKey["CenterDjango", "CenterDjango"] = models.ForeignKey(
        "CenterDjango",
        related_name=FieldNames.PATIENTS.value,
        on_delete=models.CASCADE,
    )
    if TYPE_CHECKING:
        patient_examinations: models.Manager["PExaminationDjango"]

    @property
    def ddict_class(self) -> type[PatientDataDict]:
        return PatientDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return PATIENT_MODEL_LIST_TYPE_FIELDS

    @classmethod
    def nested_fields(cls) -> list[str]:
        return PATIENT_MODEL_NESTED_FIELDS

    class Meta(PersonDjango.Meta, LedgerBaseModelDjango.Meta):
        abstract = False
