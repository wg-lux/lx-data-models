from typing import TYPE_CHECKING

from django.db import models

from lx_dtypes.models.base.app_base_model.django.KnowledgebaseBaseModelDjango import (
    KnowledgebaseBaseModelDjango,
)
from lx_dtypes.names import (
    CLASSIFICATION_CHOICE_DESCRIPTOR_MODEL_LIST_TYPE_FIELDS,
    ClassificationChoiceDescriptorTypes,
    FieldNames,
    NumericDistributionChoices,
)
from lx_dtypes.utils.django_field_types import (
    BooleanFieldType,
    CharFieldType,
    FloatFieldType,
    IntegerFieldType,
    JSONFieldType,
)

from .ClassificationChoiceDescriptorDataDict import (
    ClassificationChoiceDescriptorDataDict,
)

if TYPE_CHECKING:
    from lx_dtypes.models.knowledge_base.unit.UnitDjango import (
        UnitDjango,
    )


class ClassificationChoiceDescriptorDjango(
    KnowledgebaseBaseModelDjango[ClassificationChoiceDescriptorDataDict]
):
    classification_choice_descriptor_type: CharFieldType = models.CharField(
        max_length=32,
        choices=[
            (choice.value, choice.value)
            for choice in ClassificationChoiceDescriptorTypes
        ],
        default=ClassificationChoiceDescriptorTypes.NUMERIC.value,
    )
    numeric_distribution: CharFieldType = models.CharField(
        max_length=32,
        choices=[(choice.value, choice.value) for choice in NumericDistributionChoices],
        default=NumericDistributionChoices.UNIFORM.value,
    )
    unit: models.ForeignKey["UnitDjango", "UnitDjango"] = models.ForeignKey(
        "UnitDjango",
        related_name=FieldNames.CLASSIFICATION_CHOICE_DESCRIPTORS.value,
        on_delete=models.CASCADE,
    )

    numeric_min: FloatFieldType = models.FloatField()
    numeric_max: FloatFieldType = models.FloatField()
    numeric_distribution_params: JSONFieldType = models.JSONField()
    text_max_length: IntegerFieldType = models.IntegerField()
    default_value_str: CharFieldType = models.CharField(max_length=255)
    default_value_num: FloatFieldType = models.FloatField()
    default_value_bool: BooleanFieldType = models.BooleanField()
    selection_options: JSONFieldType = models.JSONField()
    selection_multiple: BooleanFieldType = models.BooleanField()
    selection_multiple_n_min: IntegerFieldType = models.IntegerField()
    selection_multiple_n_max: IntegerFieldType = models.IntegerField()
    selection_default_options: JSONFieldType = models.JSONField()

    # if TYPE_CHECKING:
    #     from .ClassificationChoiceDjango import (
    #         ClassificationChoiceDjango,
    #     )

    #     classification_choices: models.QuerySet["ClassificationChoiceDjango"]

    @property
    def ddict_class(self) -> type[ClassificationChoiceDescriptorDataDict]:
        return ClassificationChoiceDescriptorDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return CLASSIFICATION_CHOICE_DESCRIPTOR_MODEL_LIST_TYPE_FIELDS
