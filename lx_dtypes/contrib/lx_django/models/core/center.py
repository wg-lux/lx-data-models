from django.db import models
import uuid as uuid_module
from lx_dtypes.models.core.center import CenterDataDict

from ..base_model.base_model import AppBaseModelNamesUUIDTags
from ..typing import (
    UUIDFieldType,
    OptionalCharFieldType,
)


class Center(AppBaseModelNamesUUIDTags):
    uuid: UUIDFieldType = models.UUIDField(
        default=uuid_module.uuid4, editable=False, unique=True
    )
    examiners: OptionalCharFieldType = (
        models.CharField(  # TODO make foreign key to examiner model
            max_length=255, null=True, blank=True
        )
    )

    @property
    def ddict(self) -> type[CenterDataDict]:
        return CenterDataDict

    class Meta(AppBaseModelNamesUUIDTags.Meta):
        pass

    # def to_ddict(self) -> CenterDataDict:
    #     """Convert the Patient model instance to a PatientDataDict.

    #     Returns:
    #         PatientDataDict: The converted data dictionary.
    #     """
    #     data_dict = self._to_ddict()
    #     data_dict["center_name"] = self.center_name
    #     data_dict["external_ids"] = self.external_ids
    #     ddict = self.ddict(**data_dict)
    #     return ddict
