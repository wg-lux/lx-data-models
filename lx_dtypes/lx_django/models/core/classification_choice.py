from typing import TYPE_CHECKING, Self

from django.db import models

from lx_dtypes.models.core.classification_choice import (
    ClassificationChoiceDataDict,
)
from lx_dtypes.models.core.classification_choice_shallow import (
    ClassificationChoiceShallowDataDict,
)

from ..base_model.base_model import KnowledgebaseBaseModel

if TYPE_CHECKING:
    from lx_dtypes.lx_django.models.ledger.patient_finding_classification_choice import (
        PatientFindingClassificationChoice,
    )

    from .classification import Classification
    from .classification_choice_descriptor import ClassificationChoiceDescriptor


class ClassificationChoice(KnowledgebaseBaseModel):
    classification_choice_descriptors: models.ManyToManyField[
        "ClassificationChoiceDescriptor", "ClassificationChoiceDescriptor"
    ] = models.ManyToManyField(
        "ClassificationChoiceDescriptor",
        related_name="classification_choices",
        blank=True,
    )

    if TYPE_CHECKING:
        classifications: models.QuerySet["Classification"]
        patient_finding_classification_choices: models.QuerySet[
            "PatientFindingClassificationChoice"
        ]

    @property
    def ddict_shallow(self) -> type[ClassificationChoiceShallowDataDict]:
        return ClassificationChoiceShallowDataDict

    @property
    def ddict(self) -> type[ClassificationChoiceDataDict]:
        return ClassificationChoiceDataDict

    @classmethod
    def sync_from_ddict_shallow(
        cls,
        ddict: ClassificationChoiceShallowDataDict,
    ) -> Self:
        """Create a ClassificationChoice model instance from a ClassificationChoiceShallowDataDict.

        Args:
            ddict (ClassificationChoiceShallowDataDict): The data dictionary to create the model instance from.
        Returns:
            ClassificationChoice: The created ClassificationChoice model instance.
        """
        descriptor_names = ddict["classification_choice_descriptor_names"]
        defaults = dict(ddict)
        defaults.pop("classification_choice_descriptor_names", None)

        obj, created = cls.objects.get_or_create(uuid=ddict["uuid"], defaults=defaults)

        if not created:
            for key, value in defaults.items():
                setattr(obj, key, value)

        obj.update_classification_choice_descriptors_by_names(descriptor_names)

        return obj

    # TODO def sync_to_ddict_shallow()

    def update_classification_choice_descriptors_by_names(
        self,
        descriptor_names: list[str],
    ) -> None:
        """Update the classification_choice_descriptors ManyToManyField based on a list of names.

        Args:
            descriptor_names (list[str]): List of classification choice descriptor names.
        """
        from .classification_choice_descriptor import ClassificationChoiceDescriptor

        descriptors = ClassificationChoiceDescriptor.objects.filter(
            name__in=descriptor_names
        )
        retrieved_descriptor_names = set(descriptor.name for descriptor in descriptors)
        missing_names = set(descriptor_names) - retrieved_descriptor_names
        if missing_names:
            raise ValueError(
                f"ClassificationChoiceDescriptors with names {missing_names} do not exist."
            )
        self.classification_choice_descriptors.set(descriptors)
        self.save()

    def to_ddict_shallow(self) -> ClassificationChoiceShallowDataDict:
        """Convert the ClassificationChoice model instance to a ClassificationChoiceShallowDataDict.

        Returns:
            ClassificationChoiceShallowDataDict: The converted data dictionary.
        """
        ddict = self._to_ddict()
        ddict.pop("classification_choice_descriptors", None)
        # Serialize classification_choice_descriptor_names
        desc_names = [
            desc.name for desc in self.classification_choice_descriptors.all()
        ]
        ddict["classification_choice_descriptor_names"] = desc_names
        ddict = self.ddict_shallow(**ddict)  # type: ignore[assignment]
        return ddict  # type: ignore[return-value]
