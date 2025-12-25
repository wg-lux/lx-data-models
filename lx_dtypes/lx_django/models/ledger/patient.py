from typing import TYPE_CHECKING, Self

from django.db import models

from lx_dtypes.models.ledger.patient import PatientDataDict
from lx_dtypes.utils.factories.field_defaults import str_unknown_factory

from ..base_model.person import PersonModel
from ..typing import JSONFieldType

if TYPE_CHECKING:
    from .center import Center
    from .patient_examination import PatientExamination


class Patient(PersonModel):
    center: models.ForeignKey[
        "Center | None",
        "Center | None",
    ] = models.ForeignKey(
        "Center",
        related_name="patients",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    external_ids: JSONFieldType = models.JSONField(
        default=dict,
    )

    if TYPE_CHECKING:  # pragma: no cover
        examinations: models.QuerySet["PatientExamination"]

    @property
    def ddict(self) -> type[PatientDataDict]:
        return PatientDataDict

    class Meta(PersonModel.Meta):
        pass

    @classmethod
    def sync_from_ddict(cls, ddict: PatientDataDict) -> Self:
        """Sync a Patient model instance from a PatientDataDict.

        Args:
            ddict (PatientDataDict): The data dictionary to sync from.
        Returns:
            Patient: The synced Patient model instance.
        """
        from .center import Center

        center_name = ddict["center_name"]
        defaults = dict(ddict)
        defaults.pop("center_name", None)

        try:
            center = Center.objects.get(name=center_name)
            defaults["center"] = center
        except Center.DoesNotExist:
            raise ValueError(
                f"Patient '{ddict.get('name', '<unknown>')}' "
                f"references missing center '{center_name}'."
            )

        obj, created = cls.objects.get_or_create(uuid=ddict["uuid"], defaults=defaults)
        if not created:
            for key, value in defaults.items():
                setattr(obj, key, value)
            obj.save()

        return obj

    def to_ddict_shallow(self) -> PatientDataDict:
        """Convert the Patient model instance to a PatientDataDict.

        Returns:
            PatientDataDict: The converted data dictionary.
        """
        data_dict = self._to_ddict()
        data_dict.pop("external_ids", None)
        center_name = self.center.name if self.center else str_unknown_factory()
        data_dict["center_name"] = center_name
        data_dict.pop("center", None)
        ddict = self.ddict(**data_dict)
        return ddict
