from typing import TYPE_CHECKING, Self

from django.db import models

from lx_dtypes.models.ledger.examiner import ExaminerDataDict
from lx_dtypes.utils.factories.field_defaults import str_unknown_factory

from ..base_model.person import PersonModel
from ..typing import (
    OptionalJSONFieldType,
)

if TYPE_CHECKING:
    from .center import Center


class Examiner(PersonModel):
    center: models.ForeignKey["Center | None", "Center | None"] = models.ForeignKey(
        "Center",
        related_name="examiners",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    external_ids: OptionalJSONFieldType = models.JSONField(
        null=True, blank=True, default=dict
    )

    @property
    def ddict(self) -> type[ExaminerDataDict]:
        return ExaminerDataDict

    class Meta(PersonModel.Meta):
        pass

    @classmethod
    def sync_from_ddict(cls, ExaminerDataDict: ExaminerDataDict) -> Self:
        """Sync an Examiner model instance from an ExaminerDataDict.

        Args:
            ddict (ExaminerDataDict): The data dictionary to sync from.
        Returns:
            Examiner: The synced Examiner model instance.
        """
        from .center import Center

        center_name = ExaminerDataDict["center_name"]
        defaults = dict(ExaminerDataDict)
        defaults.pop("center_name", None)

        try:
            center = Center.objects.get(name=center_name)
            defaults["center"] = center
        except Center.DoesNotExist:
            raise ValueError(
                f"Examiner '{ExaminerDataDict.get('name', '<unknown>')}' "
                f"references missing center '{center_name}'."
            )

        obj, created = cls.objects.get_or_create(
            uuid=ExaminerDataDict["uuid"], defaults=defaults
        )

        if not created:
            for key, value in defaults.items():
                setattr(obj, key, value)
            obj.save()

        return obj

    def to_ddict_shallow(self) -> ExaminerDataDict:
        """Convert the Patient model instance to a PatientDataDict.

        Returns:
            PatientDataDict: The converted data dictionary.
        """
        data_dict = self._to_ddict()
        data_dict.pop("external_ids", None)
        data_dict.pop("center", None)
        center_name = self.center.name if self.center else str_unknown_factory()
        data_dict["center_name"] = center_name
        ddict = self.ddict(**data_dict)
        return ddict
