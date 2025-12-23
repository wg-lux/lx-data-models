from typing import TYPE_CHECKING, Self

from django.db import models

from lx_dtypes.models.core.classification import (
    ClassificationDataDict,
    ClassificationTypeDataDict,
)
from lx_dtypes.models.core.classification_shallow import (
    ClassificationShallowDataDict,
    ClassificationTypeShallowDataDict,
)

from ..base_model.base_model import KnowledgebaseBaseModel

if TYPE_CHECKING:
    from .classification_choice import ClassificationChoice
    from .examination import Examination
    from .finding import Finding


class ClassificationType(KnowledgebaseBaseModel):
    if TYPE_CHECKING:
        classifications: models.Manager["Classification"]

    @property
    def ddict_shallow(self) -> type[ClassificationTypeShallowDataDict]:
        return ClassificationTypeShallowDataDict

    @property
    def ddict(self) -> type[ClassificationTypeDataDict]:
        return ClassificationTypeDataDict

    @classmethod
    def sync_from_ddict_shallow(cls, ddict: ClassificationTypeShallowDataDict) -> Self:
        """Create a ClassificationType model instance from a ClassificationTypeShallowDataDict
        Args:
            ddict (ClassificationTypeShallowDataDict): The data dictionary to create the model instance from.
        Returns:
            ClassificationType: The created ClassificationType model instance.
        """
        obj, created = cls.objects.get_or_create(uuid=ddict["uuid"], defaults=ddict)
        if not created:
            for key, value in ddict.items():
                setattr(obj, key, value)
            obj.save()
        return obj


class Classification(KnowledgebaseBaseModel):
    choices: models.ManyToManyField["ClassificationChoice", "ClassificationChoice"] = (
        models.ManyToManyField(
            "ClassificationChoice",
            related_name="classifications",
            blank=True,
        )
    )

    types: models.ManyToManyField["ClassificationType", "ClassificationType"] = (
        models.ManyToManyField(
            ClassificationType,
            related_name="classifications",
            blank=True,
        )
    )

    if TYPE_CHECKING:
        examinations: models.Manager["Examination"]
        findings: models.Manager["Finding"]

    @property
    def ddict_shallow(self) -> type[ClassificationShallowDataDict]:
        return ClassificationShallowDataDict

    @property
    def ddict(self) -> type[ClassificationDataDict]:
        return ClassificationDataDict

    @classmethod
    def sync_from_ddict_shallow(
        cls,
        ddict: ClassificationShallowDataDict,
    ) -> Self:
        """Create a Classification model instance from a ClassificationShallowDataDict.

        Args:
            ddict (ClassificationShallowDataDict): The data dictionary to create the model instance from.
        Returns:
            Classification: The created Classification model instance.
        """
        choice_names = ddict["choice_names"]
        type_names = ddict["type_names"]

        defaults = dict(ddict)

        defaults.pop("choice_names", None)
        defaults.pop("type_names", None)

        obj, created = cls.objects.get_or_create(uuid=ddict["uuid"], defaults=defaults)

        if not created:
            for key, value in defaults.items():
                setattr(obj, key, value)

        obj.update_classification_choices_by_names(choice_names)
        obj.update_classification_types_by_names(type_names)

        return obj

    # TODO def sync_to_ddict_shallow()

    def update_classification_choices_by_names(
        self,
        choice_names: list[str],
    ) -> None:
        """Update the classification choices of the Classification model instance by their names.

        Args:
            choice_names (list[str]): The list of classification choice names to update.
        """
        from .classification_choice import ClassificationChoice

        choices = ClassificationChoice.objects.filter(name__in=choice_names)
        retrieved_choice_names = set(choice.name for choice in choices)
        missing_choices = set(choice_names) - retrieved_choice_names
        if missing_choices:
            raise ValueError(
                f"ClassificationChoices with names {missing_choices} do not exist."
            )

        self.choices.set(choices)
        self.save()

    def update_classification_types_by_names(
        self,
        type_names: list[str],
    ) -> None:
        """Update the classification types of the Classification model instance by their names.

        Args:
            type_names (list[str]): The list of classification type names to update.
        """

        types = ClassificationType.objects.filter(name__in=type_names)
        retrieved_type_names = set(type.name for type in types)
        missing_types = set(type_names) - retrieved_type_names
        if missing_types:
            raise ValueError(
                f"ClassificationTypes with names {missing_types} do not exist."
            )

        self.types.set(types)
        self.save()

    def to_ddict_shallow(self) -> ClassificationShallowDataDict:
        """Convert the Classification model instance to a ClassificationShallowDataDict.

        Returns:
            ClassificationShallowDataDict: The converted data dictionary.
        """
        ddict = self._to_ddict()

        ddict.pop("choices", None)
        ddict.pop("types", None)

        c_names = [choice.name for choice in self.choices.all()]
        t_names = [ctype.name for ctype in self.types.all()]

        ddict["choice_names"] = c_names
        ddict["type_names"] = t_names

        ddict = self.ddict_shallow(**ddict)  # type: ignore[assignment]
        return ddict  # type: ignore[return-value]
