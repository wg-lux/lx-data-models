from django.db import models

from lx_dtypes.models.core.intervention import (
    InterventionDataDict,
)
from lx_dtypes.models.core.intervention_shallow import (
    InterventionShallowDataDict,
)

from ..base_model.base_model import AppBaseModelNamesUUIDTags
from ..typing import (
    CharFieldType,
)


class InterventionType(AppBaseModelNamesUUIDTags):
    pass


class Intervention(AppBaseModelNamesUUIDTags):
    type_names: CharFieldType = models.CharField(
        max_length=2000, null=True, blank=True
    )  # store as comma-separated UUIDs

    @property
    def ddict_shallow(self) -> type[InterventionShallowDataDict]:
        return InterventionShallowDataDict

    @property
    def ddict(self) -> type[InterventionDataDict]:
        return InterventionDataDict

    def to_ddict_shallow(self) -> InterventionShallowDataDict:
        """Convert the Intervention model instance to an InterventionShallowDataDict.

        Returns:
            InterventionShallowDataDict: The converted data dictionary.
        """
        data_dict = self._to_ddict()
        data_dict["type_names"] = self.str_list_to_list(self.type_names)

        ddict = self.ddict_shallow(**data_dict)
        return ddict
