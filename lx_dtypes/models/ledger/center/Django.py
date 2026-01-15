from typing import TYPE_CHECKING

from django.db import models

from lx_dtypes.factories.literals import str_unknown_factory
from lx_dtypes.models.base.app_base_model.django.LedgerBaseModelDjango import (
    LedgerBaseModelDjango,
)
from lx_dtypes.names import (
    CENTER_MODEL_LIST_TYPE_FIELDS,
    CENTER_MODEL_NESTED_FIELDS,
)
from lx_dtypes.utils.django_field_types import CharFieldType, JSONFieldType

from .DataDict import (
    CenterDataDict,
)

if TYPE_CHECKING:
    from lx_dtypes.models.ledger.examiner.Django import (
        ExaminerDjango,
    )
    from lx_dtypes.models.ledger.patient.Django import (
        PatientDjango,
    )


class CenterDjango(LedgerBaseModelDjango[CenterDataDict]):
    name: CharFieldType = models.CharField(max_length=256, default=str_unknown_factory)
    external_ids: JSONFieldType = models.JSONField(default=dict)

    if TYPE_CHECKING:
        examiners: models.QuerySet["ExaminerDjango"]
        patients: models.QuerySet["PatientDjango"]

    @property
    def ddict_class(self) -> type[CenterDataDict]:
        return CenterDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return CENTER_MODEL_LIST_TYPE_FIELDS

    @classmethod
    def nested_fields(cls) -> list[str]:
        return CENTER_MODEL_NESTED_FIELDS

    class Meta(LedgerBaseModelDjango.Meta):
        abstract = False
