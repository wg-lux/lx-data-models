from typing import TYPE_CHECKING

from django.db import models

from lx_dtypes.models.base.app_base_model.django.LedgerBaseModelDjango import (
    LedgerBaseModelDjango,
)
from lx_dtypes.names import (
    P_FINDING_CLASSIFICATION_CHOICE_DESCRIPTOR_MODEL_LIST_TYPE_FIELDS,
    P_FINDING_CLASSIFICATION_CHOICE_DESCRIPTOR_MODEL_NESTED_FIELDS,
    FieldNames,
)
from lx_dtypes.utils.django_field_types import CharFieldType

from .DataDict import (
    PFindingClassificationChoiceDescriptorDataDict,
)

if TYPE_CHECKING:
    from lx_dtypes.models.knowledge_base.classification_choice_descriptor.ClassificationChoiceDescriptorDjango import (
        ClassificationChoiceDescriptorDjango,
    )
    from lx_dtypes.models.ledger.p_finding_classification_choice.Django import (
        PFindingClassificationChoiceDjango,
    )


class PFindingClassificationChoiceDescriptorDjango(
    LedgerBaseModelDjango[PFindingClassificationChoiceDescriptorDataDict]
):
    descriptor_value: CharFieldType = models.CharField(max_length=255)
    classification_choice_descriptor: models.ForeignKey[
        "ClassificationChoiceDescriptorDjango", "ClassificationChoiceDescriptorDjango"
    ] = models.ForeignKey(
        "ClassificationChoiceDescriptorDjango",
        related_name=FieldNames.PATIENT_FINDING_CLASSIFICATION_CHOICE_DESCRIPTORS.value,
        on_delete=models.CASCADE,
    )
    patient_finding_classification_choice: models.ForeignKey[
        "PFindingClassificationChoiceDjango", "PFindingClassificationChoiceDjango"
    ] = models.ForeignKey(
        "PFindingClassificationChoiceDjango",
        related_name=FieldNames.PATIENT_FINDING_CLASSIFICATION_CHOICE_DESCRIPTORS.value,
        on_delete=models.CASCADE,
    )

    @property
    def ddict_class(self) -> type[PFindingClassificationChoiceDescriptorDataDict]:
        return PFindingClassificationChoiceDescriptorDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return P_FINDING_CLASSIFICATION_CHOICE_DESCRIPTOR_MODEL_LIST_TYPE_FIELDS

    @classmethod
    def nested_fields(cls) -> list[str]:
        return P_FINDING_CLASSIFICATION_CHOICE_DESCRIPTOR_MODEL_NESTED_FIELDS

    class Meta(LedgerBaseModelDjango.Meta):
        abstract = False
