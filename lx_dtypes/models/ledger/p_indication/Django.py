from typing import TYPE_CHECKING

from django.db import models

from lx_dtypes.models.base.app_base_model.django.LedgerBaseModelDjango import (
    LedgerBaseModelDjango,
)
from lx_dtypes.names import (
    P_INDICATION_MODEL_LIST_TYPE_FIELDS,
    P_INDICATION_MODEL_NESTED_FIELDS,
    FieldNames,
)

from .DataDict import (
    PIndicationDataDict,
)

if TYPE_CHECKING:
    from lx_dtypes.models.knowledge_base.indication.IndicationDjango import (
        IndicationDjango,
    )
    from lx_dtypes.models.ledger.p_examination.Django import (
        PExaminationDjango,
    )


class PIndicationDjango(LedgerBaseModelDjango[PIndicationDataDict]):
    indication: models.ForeignKey["IndicationDjango", "IndicationDjango"] = (
        models.ForeignKey(
            "IndicationDjango",
            related_name=FieldNames.PATIENT_INDICATIONS.value,
            on_delete=models.CASCADE,
        )
    )
    patient_examination: models.ForeignKey[
        "PExaminationDjango", "PExaminationDjango"
    ] = models.ForeignKey(
        "PExaminationDjango",
        related_name=FieldNames.PATIENT_INDICATIONS.value,
        on_delete=models.CASCADE,
    )

    @property
    def ddict_class(self) -> type[PIndicationDataDict]:
        return PIndicationDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return P_INDICATION_MODEL_LIST_TYPE_FIELDS

    @classmethod
    def nested_fields(cls) -> list[str]:
        return P_INDICATION_MODEL_NESTED_FIELDS

    class Meta(LedgerBaseModelDjango.Meta):
        abstract = False
