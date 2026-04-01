from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

from lx_dtypes.models.base.app_base_model.django.LedgerBaseModelDjango import (
    LedgerBaseModelDjango,
)
from lx_dtypes.names import (
    P_INDICATION_CLASSIFICATION_DESCRIPTOR_MODEL_LIST_TYPE_FIELDS,
    P_INDICATION_CLASSIFICATION_DESCRIPTOR_MODEL_NESTED_FIELDS,
    FieldNames,
)
from lx_dtypes.utils.django_field_types import CharFieldType

from .DataDict import PIndicationClassificationDescriptorDataDict

if TYPE_CHECKING:
    from lx_dtypes.models.knowledge_base.classification_choice_descriptor.ClassificationChoiceDescriptorDjango import (
        ClassificationChoiceDescriptorDjango,
    )
    from lx_dtypes.models.ledger.p_indication_classification.Django import (
        PIndicationClassificationDjango,
    )


class PIndicationClassificationDescriptorDjango(
    LedgerBaseModelDjango[PIndicationClassificationDescriptorDataDict]
):
    if TYPE_CHECKING:
        classification_choice_descriptor: models.ForeignKey[
            ClassificationChoiceDescriptorDjango, ClassificationChoiceDescriptorDjango
        ]
        patient_indication_classification: models.ForeignKey[
            PIndicationClassificationDjango, PIndicationClassificationDjango
        ]

    descriptor_value: CharFieldType = models.CharField(max_length=255)
    classification_choice_descriptor = models.ForeignKey(
        "ClassificationChoiceDescriptorDjango",
        related_name=FieldNames.PATIENT_INDICATION_CLASSIFICATION_DESCRIPTORS.value,
        on_delete=models.CASCADE,
    )
    patient_indication_classification = models.ForeignKey(
        "PIndicationClassificationDjango",
        related_name=FieldNames.PATIENT_INDICATION_CLASSIFICATION_DESCRIPTORS.value,
        on_delete=models.CASCADE,
    )

    @property
    def ddict_class(self) -> type[PIndicationClassificationDescriptorDataDict]:
        return PIndicationClassificationDescriptorDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return P_INDICATION_CLASSIFICATION_DESCRIPTOR_MODEL_LIST_TYPE_FIELDS

    @classmethod
    def nested_fields(cls) -> list[str]:
        return P_INDICATION_CLASSIFICATION_DESCRIPTOR_MODEL_NESTED_FIELDS

    class Meta(LedgerBaseModelDjango.Meta):
        abstract = False
