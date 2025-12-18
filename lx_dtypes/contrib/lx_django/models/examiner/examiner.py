from django.db import models

from lx_dtypes.models.examiner.examiner import ExaminerDataDict

from ..base_model.person import PersonModel
from ..typing import (
    JSONFieldType,
    OptionalCharFieldType,
)


class Examiner(PersonModel):
    center_name: OptionalCharFieldType = (
        models.CharField(  # TODO make foreign key to center model
            max_length=255, null=True, blank=True
        )
    )
    external_ids: JSONFieldType = models.JSONField(null=True, blank=True, default=dict)

    @property
    def ddict(self) -> type[ExaminerDataDict]:
        return ExaminerDataDict

    class Meta(PersonModel.Meta):
        pass

    def to_ddict(self) -> ExaminerDataDict:
        """Convert the Patient model instance to a PatientDataDict.

        Returns:
            PatientDataDict: The converted data dictionary.
        """
        data_dict = self._to_ddict()
        data_dict["center_name"] = self.center_name
        data_dict["external_ids"] = self.external_ids
        ddict = self.ddict(**data_dict)
        return ddict
