from django.db import models

from lx_dtypes.models.core.finding import FindingDataDict, FindingTypeDataDict
from lx_dtypes.models.core.finding_shallow import (
    FindingShallowDataDict,
    FindingTypeShallowDataDict,
)

from ..base_model.base_model import KnowledgeBaseModel
from ..typing import OptionalCharFieldType


class FindingType(KnowledgeBaseModel):
    pass

    @property
    def ddict(self) -> type[FindingTypeDataDict]:
        return FindingTypeDataDict

    @property
    def ddict_shallow(self) -> type[FindingTypeShallowDataDict]:
        return FindingTypeShallowDataDict


class Finding(KnowledgeBaseModel):
    classification_names: OptionalCharFieldType = models.CharField(
        max_length=2000, null=True, blank=True
    )  # store as comma-separated UUIDs

    type_names: OptionalCharFieldType = models.CharField(
        max_length=2000, null=True, blank=True
    )  # store as comma-separated UUIDs

    intervention_names: OptionalCharFieldType = models.CharField(
        max_length=2000, null=True, blank=True
    )  # store as comma-separated UUIDs

    @property
    def ddict_shallow(self) -> type[FindingShallowDataDict]:
        return FindingShallowDataDict

    @property
    def ddict(self) -> type[FindingDataDict]:
        return FindingDataDict

    def to_ddict_shallow(self) -> FindingShallowDataDict:
        """Convert the Finding model instance to a FindingShallowDataDict.

        Returns:
            FindingShallowDataDict: The converted data dictionary.
        """
        data_dict = self._to_ddict()
        data_dict["classification_names"] = self.str_list_to_list(
            self.classification_names
        )
        data_dict["type_names"] = self.str_list_to_list(self.type_names)

        data_dict["intervention_names"] = self.str_list_to_list(self.intervention_names)

        ddict = self.ddict_shallow(**data_dict)
        return ddict
