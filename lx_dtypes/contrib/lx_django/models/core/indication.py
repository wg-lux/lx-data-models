from django.db import models

from lx_dtypes.models.core.indication import (
    IndicationDataDict,
    IndicationTypeDataDict,
)
from lx_dtypes.models.core.indication_shallow import (
    IndicationShallowDataDict,
    IndicationTypeShallowDataDict,
)

from ..base_model.base_model import KnowledgeBaseModel
from ..typing import (
    CharFieldType,
)


class IndicationType(KnowledgeBaseModel):
    @property
    def ddict_shallow(self) -> type[IndicationTypeShallowDataDict]:
        return IndicationTypeShallowDataDict

    @property
    def ddict(self) -> type[IndicationTypeDataDict]:
        return IndicationTypeDataDict


class Indication(KnowledgeBaseModel):
    expected_intervention_names: CharFieldType = models.CharField(
        max_length=2000, null=True, blank=True
    )  # store as comma-separated UUIDs

    type_names: CharFieldType = models.CharField(
        max_length=2000, null=True, blank=True
    )  # store as comma-separated UUIDs

    @property
    def ddict_shallow(self) -> type[IndicationShallowDataDict]:
        return IndicationShallowDataDict

    @property
    def ddict(self) -> type[IndicationDataDict]:
        return IndicationDataDict

    def to_ddict_shallow(self) -> IndicationShallowDataDict:
        """Convert the Indication model instance to a IndicationShallowDataDict.

        Returns:
            IndicationShallowDataDict: The converted data dictionary.
        """
        data_dict = self._to_ddict()
        data_dict["expected_intervention_names"] = self.str_list_to_list(
            self.expected_intervention_names
        )
        data_dict["type_names"] = self.str_list_to_list(self.type_names)

        ddict = self.ddict_shallow(**data_dict)
        return ddict
