from django.db import models

from lx_dtypes.models.ledger.patient import PatientDataDict

from ..base_model.person import PersonModel
from ..typing import (
    OptionalCharFieldType,
    OptionalJSONFieldType,
)


class Patient(PersonModel):
    center_name: OptionalCharFieldType = (
        models.CharField(  # TODO make foreign key to center model
            max_length=255, null=True, blank=True
        )
    )
    external_ids: OptionalJSONFieldType = models.JSONField(
        null=True, blank=True, default=dict
    )

    @property
    def ddict(self) -> type[PatientDataDict]:
        return PatientDataDict

    class Meta(PersonModel.Meta):
        pass

    def to_ddict_shallow(self) -> PatientDataDict:
        """Convert the Patient model instance to a PatientDataDict.

        Returns:
            PatientDataDict: The converted data dictionary.
        """
        data_dict = self._to_ddict()
        data_dict.pop("external_ids", None)
        ddict = self.ddict(**data_dict)
        return ddict
