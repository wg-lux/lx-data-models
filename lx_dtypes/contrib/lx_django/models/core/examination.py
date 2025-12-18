from django.db import models

from lx_dtypes.models.core.examination import (
    ExaminationDataDict,
    ExaminationTypeDataDict,
)
from lx_dtypes.models.core.examination_shallow import (
    ExaminationShallowDataDict,
    ExaminationTypeShallowDataDict,
)

from ..base_model.base_model import AppBaseModelNamesUUIDTags
from ..typing import (
    CharFieldType,
)


class ExaminationType(AppBaseModelNamesUUIDTags):
    @property
    def ddict_shallow(self) -> type[ExaminationTypeShallowDataDict]:
        return ExaminationTypeShallowDataDict

    @property
    def ddict(self) -> type[ExaminationTypeDataDict]:
        return ExaminationTypeDataDict


class Examination(AppBaseModelNamesUUIDTags):
    finding_names: CharFieldType = models.CharField(
        max_length=2000, null=True, blank=True
    )  # store as comma-separated UUIDs

    type_names: CharFieldType = models.CharField(
        max_length=2000, null=True, blank=True
    )  # store as comma-separated UUIDs

    indication_names: CharFieldType = models.CharField(
        max_length=2000, null=True, blank=True
    )  # store as comma-separated UUIDs

    @property
    def ddict_shallow(self) -> type[ExaminationShallowDataDict]:
        return ExaminationShallowDataDict

    @property
    def ddict(self) -> type[ExaminationDataDict]:
        return ExaminationDataDict

    def to_ddict_shallow(self) -> ExaminationShallowDataDict:
        """Convert the Examination model instance to a ExaminationShallowDataDict.

        Returns:
            ExaminationShallowDataDict: The converted data dictionary.
        """
        data_dict = self._to_ddict()
        data_dict["finding_names"] = self.str_list_to_list(self.finding_names)
        data_dict["type_names"] = self.str_list_to_list(self.type_names)
        data_dict["indication_names"] = self.str_list_to_list(self.indication_names)

        ddict = self.ddict_shallow(**data_dict)
        return ddict
