from django.db import models

from lx_dtypes.models.core.information_source import (
    InformationSourceDataDict,
    InformationSourceTypeDataDict,
)
from lx_dtypes.models.core.information_source_shallow import (
    InformationSourceShallowDataDict,
    InformationSourceTypeShallowDataDict,
)

from ..base_model.base_model import KnowledgeBaseModel
from ..typing import (
    CharFieldType,
)


class InformationSourceType(KnowledgeBaseModel):
    @property
    def ddict_shallow(self) -> type[InformationSourceTypeShallowDataDict]:
        return InformationSourceTypeShallowDataDict

    @property
    def ddict(self) -> type[InformationSourceTypeDataDict]:
        return InformationSourceTypeDataDict


class InformationSource(KnowledgeBaseModel):
    type_names: CharFieldType = models.CharField(
        max_length=2000, null=True, blank=True
    )  # store as comma-separated UUIDs

    @property
    def ddict_shallow(self) -> type[InformationSourceShallowDataDict]:
        return InformationSourceShallowDataDict

    @property
    def ddict(self) -> type[InformationSourceDataDict]:
        return InformationSourceDataDict

    def to_ddict_shallow(self) -> InformationSourceShallowDataDict:
        """Convert the InformationSource model instance to a InformationSourceShallowDataDict.

        Returns:
            InformationSourceShallowDataDict: The converted data dictionary.
        """
        data_dict = self._to_ddict()
        data_dict["type_names"] = self.str_list_to_list(self.type_names)

        ddict = self.ddict_shallow(**data_dict)
        return ddict
