from django.db import models

from lx_dtypes.models.core.classification import (
    ClassificationDataDict,
    ClassificationTypeDataDict,
)
from lx_dtypes.models.core.classification_shallow import (
    ClassificationShallowDataDict,
    ClassificationTypeShallowDataDict,
)

from ..base_model.base_model import KnowledgeBaseModel
from ..typing import (
    CharFieldType,
)


class ClassificationType(KnowledgeBaseModel):
    @property
    def ddict_shallow(self) -> type[ClassificationTypeShallowDataDict]:
        return ClassificationTypeShallowDataDict

    @property
    def ddict(self) -> type[ClassificationTypeDataDict]:
        return ClassificationTypeDataDict


class Classification(KnowledgeBaseModel):
    choice_names: CharFieldType = models.CharField(
        max_length=2000, null=True, blank=True
    )  # store as comma-separated UUIDs

    type_names: CharFieldType = models.CharField(
        max_length=2000, null=True, blank=True
    )  # store as comma-separated UUIDs

    @property
    def ddict_shallow(self) -> type[ClassificationShallowDataDict]:
        return ClassificationShallowDataDict

    @property
    def ddict(self) -> type[ClassificationDataDict]:
        return ClassificationDataDict

    def to_ddict_shallow(self) -> ClassificationShallowDataDict:
        """Convert the Classification model instance to a ClassificationShallowDataDict.

        Returns:
            ClassificationShallowDataDict: The converted data dictionary.
        """
        data_dict = self._to_ddict()
        data_dict["choice_names"] = self.str_list_to_list(self.choice_names)
        data_dict["type_names"] = self.str_list_to_list(self.type_names)

        ddict = self.ddict_shallow(**data_dict)
        return ddict
