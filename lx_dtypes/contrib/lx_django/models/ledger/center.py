import uuid as uuid_module
from typing import TYPE_CHECKING, List, Self

from django.db import models

from lx_dtypes.models.ledger.center import CenterDataDict
from lx_dtypes.models.ledger.center_shallow import CenterShallowDataDict

from ..base_model.base_model import AppBaseModelNamesUUIDTags

if TYPE_CHECKING:
    from .examiner import Examiner
    from .patient import Patient


class Center(AppBaseModelNamesUUIDTags):
    @property
    def ddict(self) -> type[CenterDataDict]:
        return CenterDataDict

    @property
    def ddict_shallow(self) -> type[CenterShallowDataDict]:
        return CenterShallowDataDict

    if TYPE_CHECKING:  # pragma: no cover
        examiners: models.QuerySet["Examiner"]  # Related field from Examiner model
        patients: models.QuerySet["Patient"]  # Related field from Patient model

    def sync_linked_examiners_by_uuids(self, examiner_uuid_str_list: List[str]) -> None:
        """Sync linked examiners by their UUIDs.

        Args:
            examiner_uuids (List[str]): List of examiner UUIDs to link.
        """
        from .examiner import Examiner

        examiner_uuids = [
            uuid_module.UUID(examiner_uuid_str)
            for examiner_uuid_str in examiner_uuid_str_list
        ]

        # Link examiners to this center
        Examiner.objects.filter(uuid__in=examiner_uuids).update(center=self)
        # Unlink examiners that are no longer associated
        self.examiners.exclude(uuid__in=examiner_uuids).update(center=None)

    @classmethod
    def sync_from_ddict(
        cls,
        ddict: CenterDataDict,
    ) -> Self:
        """Sync a Center model instance from a CenterShallowDataDict.

        Args:
            ddict (CenterShallowDataDict): The data dictionary to sync from.)
        Returns:
            Center: The synced Center model instance.
        """
        from .examiner import Examiner

        examiners = ddict["examiners"]

        defaults = dict(ddict)
        defaults.pop("examiners", None)
        defaults.pop("examiner_uuids", None)

        obj, created = cls.objects.get_or_create(uuid=ddict["uuid"], defaults=defaults)
        if not created:
            for key, value in ddict.items():
                setattr(obj, key, value)
            obj.save()

        for examiner_uuid_str, examiner in examiners.items():
            Examiner.sync_from_ddict(examiner)

        return obj

    def to_ddict_shallow(self) -> CenterShallowDataDict:
        """Convert the Center model instance to a CenterShallowDataDict.

        Returns:
            CenterShallowDataDict: The converted data dictionary.
        """
        data_dict = self._to_ddict()
        examiner_uuids = [str(examiner.uuid) for examiner in self.examiners.all()]
        data_dict["examiner_uuids"] = examiner_uuids
        ddict = self.ddict_shallow(**data_dict)
        return ddict
