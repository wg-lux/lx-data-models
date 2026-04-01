from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

from lx_dtypes.models.base.app_base_model.django.LedgerBaseModelDjango import (
    LedgerBaseModelDjango,
)
from lx_dtypes.names import (
    P_INDICATION_CLASSIFICATION_MODEL_LIST_TYPE_FIELDS,
    P_INDICATION_CLASSIFICATION_MODEL_NESTED_FIELDS,
    FieldNames,
)

from .DataDict import PIndicationClassificationDataDict

if TYPE_CHECKING:
    from lx_dtypes.models.knowledge_base.classification._ClassificationDjango import (
        ClassificationDjango,
    )
    from lx_dtypes.models.knowledge_base.classification_choice.ClassificationChoiceDjango import (
        ClassificationChoiceDjango,
    )
    from lx_dtypes.models.ledger.p_indication.Django import PIndicationDjango
    from lx_dtypes.models.ledger.p_indication_classification_descriptor.Django import (
        PIndicationClassificationDescriptorDjango,
    )


class PIndicationClassificationDjango(
    LedgerBaseModelDjango[PIndicationClassificationDataDict]
):
    if TYPE_CHECKING:
        classification: models.ForeignKey[ClassificationDjango, ClassificationDjango]
        classification_choice: models.ForeignKey[
            ClassificationChoiceDjango, ClassificationChoiceDjango
        ]
        patient_indication: models.ForeignKey[PIndicationDjango, PIndicationDjango]
        patient_indication_classification_descriptors: models.Manager[
            PIndicationClassificationDescriptorDjango
        ]

    classification = models.ForeignKey(
        "ClassificationDjango",
        related_name=FieldNames.PATIENT_INDICATION_CLASSIFICATIONS.value,
        on_delete=models.CASCADE,
    )
    classification_choice = models.ForeignKey(
        "lx_dtypes_django.ClassificationChoiceDjango",
        related_name=FieldNames.PATIENT_INDICATION_CLASSIFICATIONS.value,
        on_delete=models.CASCADE,
    )
    patient_indication = models.ForeignKey(
        "PIndicationDjango",
        related_name=FieldNames.PATIENT_INDICATION_CLASSIFICATIONS.value,
        on_delete=models.CASCADE,
    )

    @property
    def ddict_class(self) -> type[PIndicationClassificationDataDict]:
        return PIndicationClassificationDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return P_INDICATION_CLASSIFICATION_MODEL_LIST_TYPE_FIELDS

    @classmethod
    def nested_fields(cls) -> list[str]:
        return P_INDICATION_CLASSIFICATION_MODEL_NESTED_FIELDS

    class Meta(LedgerBaseModelDjango.Meta):
        abstract = False
