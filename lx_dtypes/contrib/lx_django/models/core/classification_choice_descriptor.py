from django.db import models

from lx_dtypes.models.core.classification_choice_descriptor import (
    ClassificationChoiceDescriptorDataDict,
)
from lx_dtypes.models.core.classification_choice_descriptor_shallow import (
    ClassificationChoiceDescriptorShallowDataDict,
)

from ..base_model.base_model import KnowledgeBaseModel
from ..typing import (
    BooleanFieldType,
    CharFieldType,
    FloatFieldType,
    IntegerFieldType,
    JSONFieldType,
    OptionalCharFieldType,
    OptionalFloatFieldType,
    OptionalIntegerFieldType,
)


class ClassificationChoiceDescriptor(KnowledgeBaseModel):
    descriptor_type: OptionalCharFieldType = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        choices=[
            ("numeric", "numeric"),
            ("text", "text"),
            ("boolean", "boolean"),
            ("selection", "selection"),
        ],
    )
    unit_name: OptionalCharFieldType = models.CharField(
        max_length=255, null=True, blank=True
    )
    numeric_min: OptionalFloatFieldType = models.FloatField(null=True, blank=True)
    numeric_max: OptionalFloatFieldType = models.FloatField(null=True, blank=True)

    numeric_distribution: OptionalCharFieldType = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        choices=[
            ("normal", "normal"),
            ("uniform", "uniform"),
            ("exponential", "exponential"),
            ("unknown", "unknown"),
        ],
    )

    numeric_distribution_params: JSONFieldType = models.JSONField(
        default=dict, blank=True
    )
    text_max_length: OptionalIntegerFieldType = models.IntegerField(
        null=True, blank=True
    )

    default_value_str: CharFieldType = models.CharField(
        max_length=255,
    )

    default_value_num: FloatFieldType = models.FloatField()
    default_value_bool: BooleanFieldType = models.BooleanField()
    selection_options: CharFieldType = models.CharField(
        max_length=1000,
    )  # Comma-separated options wrapped by "[" and "]"

    selection_multiple: BooleanFieldType = models.BooleanField(default=False)
    selection_multiple_n_min: IntegerFieldType = models.IntegerField(
        null=True, blank=True
    )
    selection_multiple_n_max: IntegerFieldType = models.IntegerField(
        null=True, blank=True
    )
    selection_default_options: JSONFieldType = models.JSONField(
        default=dict, blank=True
    )

    @property
    def ddict(self) -> type[ClassificationChoiceDescriptorDataDict]:
        return ClassificationChoiceDescriptorDataDict

    @property
    def ddict_shallow(self) -> type[ClassificationChoiceDescriptorShallowDataDict]:
        return ClassificationChoiceDescriptorShallowDataDict

    def to_ddict_shallow(self) -> ClassificationChoiceDescriptorShallowDataDict:
        """Convert the ClassificationChoiceDescriptor model instance to a ClassificationChoiceDescriptorDataDict.

        Returns:
            ClassificationChoiceDescriptorDataDict: The converted data dictionary.
        """
        data_dict = self._to_ddict()
        data_dict["selection_options"] = self.str_list_to_list(self.selection_options)
        ddict = self.ddict_shallow(**data_dict)
        return ddict
