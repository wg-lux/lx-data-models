from typing import TYPE_CHECKING, Self

from django.db import models

from lx_dtypes.models.core.classification_choice_descriptor import (
    ClassificationChoiceDescriptorDataDict,
)
from lx_dtypes.models.core.classification_choice_descriptor_shallow import (
    ClassificationChoiceDescriptorShallowDataDict,
)

from ..base_model.base_model import KnowledgebaseBaseModel
from ..typing import (
    BooleanFieldType,
    CharFieldType,
    FloatFieldType,
    JSONFieldType,
    OptionalCharFieldType,
    OptionalFloatFieldType,
    OptionalIntegerFieldType,
)

if TYPE_CHECKING:
    from lx_dtypes.lx_django.models.ledger.patient_finding_classification_choice_descriptor import (
        PatientFindingClassificationChoiceDescriptor,
    )

    from .classification_choice import ClassificationChoice
    from .unit import Unit


class ClassificationChoiceDescriptor(KnowledgebaseBaseModel):
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
    unit: models.ForeignKey[
        "Unit | None",
        "Unit | None",
    ] = models.ForeignKey(
        "Unit",
        related_name="classification_choice_descriptors",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
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
    selection_multiple_n_min: OptionalIntegerFieldType = models.IntegerField(
        null=True, blank=True
    )
    selection_multiple_n_max: OptionalIntegerFieldType = models.IntegerField(
        null=True, blank=True
    )
    selection_default_options: JSONFieldType = models.JSONField(
        default=dict, blank=True
    )

    if TYPE_CHECKING:
        classification_choices: models.Manager["ClassificationChoice"]
        patient_finding_classification_choice_descriptors: models.QuerySet[
            "PatientFindingClassificationChoiceDescriptor"
        ]

    @property
    def ddict(self) -> type[ClassificationChoiceDescriptorDataDict]:
        return ClassificationChoiceDescriptorDataDict

    @property
    def ddict_shallow(self) -> type[ClassificationChoiceDescriptorShallowDataDict]:
        return ClassificationChoiceDescriptorShallowDataDict

    @classmethod
    def sync_from_ddict_shallow(
        cls, ddict: ClassificationChoiceDescriptorShallowDataDict
    ) -> Self:
        """Create a ClassificationChoiceDescriptor model instance from a ClassificationChoiceDescriptorDataDict.

        Args:
            ddict (ClassificationChoiceDescriptorDataDict): The data dictionary to create the model instance from.
        Returns:
            ClassificationChoiceDescriptor: The created ClassificationChoiceDescriptor model instance.
        """
        from .unit import Unit

        unit_name = ddict["unit_name"]
        defaults = dict(ddict)
        defaults.pop("unit_name", None)
        descriptor_name = ddict.get("name", "<unknown>")
        module_name = ddict.get("kb_module_name", "<unknown>")
        if unit_name:
            try:
                unit = Unit.get_by_name(unit_name)
                defaults["unit"] = unit
            except Unit.DoesNotExist:
                raise ValueError(
                    f"ClassificationChoiceDescriptor '{descriptor_name}' "
                    f"(module '{module_name}') references missing unit '{unit_name}'."
                )

        obj, created = cls.objects.get_or_create(uuid=ddict["uuid"], defaults=defaults)

        if not created:
            for key, value in defaults.items():
                setattr(obj, key, value)
            obj.save()

        return obj

    # def sync_to_ddict_shallow(
    #     self, ddict: ClassificationChoiceDescriptorShallowDataDict
    # ) -> ClassificationChoiceDescriptorShallowDataDict:
    #     """
    #     Sync the ClassificationChoiceDescriptor model instance to a ClassificationChoiceDescriptorDataDict.
    #     Args:
    #         ddict (ClassificationChoiceDescriptorDataDict): The data dictionary to sync the model instance to.
    #     """
    #     data_dict = self.to_ddict_shallow()
    #     assert data_dict["uuid"] == ddict["uuid"]

    #     for key, value in data_dict.items():
    #         ddict[key] = value
    #     return ddict

    def to_ddict_shallow(self) -> ClassificationChoiceDescriptorShallowDataDict:
        """Convert the ClassificationChoiceDescriptor model instance to a ClassificationChoiceDescriptorDataDict.

        Returns:
            ClassificationChoiceDescriptorDataDict: The converted data dictionary.
        """
        data_dict = self._to_ddict()
        data_dict["selection_options"] = self.str_list_to_list(self.selection_options)
        ddict = self.ddict_shallow(**data_dict)
        return ddict
