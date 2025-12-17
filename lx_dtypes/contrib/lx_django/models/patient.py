from django.db import models

from lx_dtypes.models.patient.patient import PatientDataDict

from .base_models import PersonModel
from .typing import (
    JSONFieldType,
    OptionalCharFieldType,
)


class Patient(PersonModel):
    center_name: OptionalCharFieldType = models.CharField(
        max_length=255, null=True, blank=True
    )
    external_ids: JSONFieldType = models.JSONField(null=True, blank=True, default=dict)

    @property
    def ddict(self) -> type[PatientDataDict]:
        return PatientDataDict

    class Meta(PersonModel.Meta):
        pass

    def to_ddict(self) -> PatientDataDict:
        """Convert the Patient model instance to a PatientDataDict.

        Returns:
            PatientDataDict: The converted data dictionary.
        """
        data_dict = self._to_ddict()
        data_dict["center_name"] = self.center_name
        data_dict["external_ids"] = self.external_ids
        ddict = self.ddict(**data_dict)
        return ddict
