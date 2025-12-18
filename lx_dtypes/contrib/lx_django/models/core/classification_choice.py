from django.db import models

from lx_dtypes.models.core.classification_choice import (
    ClassificationChoiceDataDict,
)
from lx_dtypes.models.core.classification_choice_shallow import (
    ClassificationChoiceShallowDataDict,
)

from ..base_model.base_model import AppBaseModelNamesUUIDTags
from ..typing import (
    CharFieldType,
)


class ClassificationChoice(AppBaseModelNamesUUIDTags):
    classification_choice_descriptor_names: CharFieldType = models.CharField(
        max_length=2000, null=True, blank=True
    )  # store as comma-separated UUIDs

    @property
    def ddict_shallow(self) -> type[ClassificationChoiceShallowDataDict]:
        return ClassificationChoiceShallowDataDict

    @property
    def ddict(self) -> type[ClassificationChoiceDataDict]:
        return ClassificationChoiceDataDict

    def to_ddict_shallow(self) -> ClassificationChoiceShallowDataDict:
        """Convert the ClassificationChoice model instance to a ClassificationChoiceShallowDataDict.

        Returns:
            ClassificationChoiceShallowDataDict: The converted data dictionary.
        """
        data_dict = self._to_ddict()
        data_dict["classification_choice_descriptor_names"] = self.str_list_to_list(
            self.classification_choice_descriptor_names
        )
        ddict = self.ddict_shallow(**data_dict)
        return ddict
