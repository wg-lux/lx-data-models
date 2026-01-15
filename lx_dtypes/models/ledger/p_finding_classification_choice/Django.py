from typing import TYPE_CHECKING

from django.db import models

from lx_dtypes.models.base.app_base_model.django.LedgerBaseModelDjango import (
    LedgerBaseModelDjango,
)
from lx_dtypes.names import (
    P_FINDING_CLASSIFICATION_CHOICE_MODEL_LIST_TYPE_FIELDS,
    P_FINDING_CLASSIFICATION_CHOICE_MODEL_NESTED_FIELDS,
    FieldNames,
)

from .DataDict import (
    PFindingClassificationChoiceDataDict,
)

if TYPE_CHECKING:
    from lx_dtypes.models.knowledge_base.classification._ClassificationDjango import (
        ClassificationDjango,
    )
    from lx_dtypes.models.knowledge_base.classification_choice.ClassificationChoiceDjango import (
        ClassificationChoiceDjango,
    )
    from lx_dtypes.models.ledger.p_finding_classification_choice_descriptor.Django import (
        PFindingClassificationChoiceDescriptorDjango,
    )
    from lx_dtypes.models.ledger.p_finding_classifications.Django import (
        PFindingClassificationsDjango,
    )


class PFindingClassificationChoiceDjango(
    LedgerBaseModelDjango[PFindingClassificationChoiceDataDict]
):
    classification: models.ForeignKey[
        "ClassificationDjango", "ClassificationDjango"
    ] = models.ForeignKey(
        "ClassificationDjango",
        related_name=FieldNames.PATIENT_FINDING_CLASSIFICATION_CHOICES.value,
        on_delete=models.CASCADE,
    )
    classification_choice: models.ForeignKey[
        "ClassificationChoiceDjango", "ClassificationChoiceDjango"
    ] = models.ForeignKey(
        "ClassificationChoiceDjango",
        related_name=FieldNames.PATIENT_FINDING_CLASSIFICATION_CHOICES.value,
        on_delete=models.CASCADE,
    )

    patient_finding_classifications: models.ForeignKey[
        "PFindingClassificationsDjango", "PFindingClassificationsDjango"
    ] = models.ForeignKey(
        "PFindingClassificationsDjango",
        related_name=FieldNames.PATIENT_FINDING_CLASSIFICATION_CHOICES.value,
        on_delete=models.CASCADE,
    )

    if TYPE_CHECKING:
        patient_finding_classification_choice_descriptors: models.Manager[
            "PFindingClassificationChoiceDescriptorDjango"
        ]

    @property
    def ddict_class(self) -> type[PFindingClassificationChoiceDataDict]:
        return PFindingClassificationChoiceDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return P_FINDING_CLASSIFICATION_CHOICE_MODEL_LIST_TYPE_FIELDS

    @classmethod
    def nested_fields(cls) -> list[str]:
        return P_FINDING_CLASSIFICATION_CHOICE_MODEL_NESTED_FIELDS

    class Meta(LedgerBaseModelDjango.Meta):
        abstract = False
