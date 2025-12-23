from typing import TYPE_CHECKING, Any, Dict, Self


from lx_dtypes.models.ledger.patient_classification_choice_descriptor import (
    PatientFindingClassificationChoiceDescriptorDataDict as PfccdDDict,
)
from lx_dtypes.models.ledger.patient_classification_choice_descriptor import (
    PatientFindingClassificationChoiceDescriptorShallowDataDict as PfccdShallowDDict,
)

from ..base_model.base_model import AppBaseModelNamesUUIDTags

if TYPE_CHECKING:
    pass

DDICT = PfccdDDict
SHALLOW_DDICT = PfccdShallowDDict


class PatientFindingClassificationChoiceDescriptor(AppBaseModelNamesUUIDTags):
    @property
    def ddict(self) -> type[DDICT]:
        return DDICT

    @property
    def ddict_shallow(self) -> type[SHALLOW_DDICT]:
        return SHALLOW_DDICT

    if TYPE_CHECKING:  # pragma: no cover
        pass

    @classmethod
    def _ddict_to_defaults(cls, ddict: DDICT) -> Dict[str, Any]:
        defaults = dict(ddict)

        defaults.pop("patient_uuid", None)
        defaults.pop("patient_examination_uuid", None)
        defaults.pop("patient_finding_uuid", None)
        defaults.pop("patient_finding_classifications_uuid", None)
        defaults.pop("patient_finding_classification_choice_uuid", None)
        defaults.pop("descriptor_name", None)

        defaults["descriptor_id"] = ddict["descriptor"]["uuid"]

        return defaults

    @classmethod
    def sync_from_ddict(
        cls,
        ddict: DDICT,
    ) -> Self:
        """Sync a Center model instance from a CenterShallowDataDict.

        Args:
            ddict (CenterShallowDataDict): The data dictionary to sync from.)
        Returns:
            Center: The synced Center model instance.
        """

        defaults = cls._ddict_to_defaults(ddict)
        obj, created = cls.objects.get_or_create(uuid=ddict["uuid"], defaults=defaults)
        if not created:
            for key, value in ddict.items():
                setattr(obj, key, value)
            obj.save()

        return obj

    def to_ddict_shallow(self) -> SHALLOW_DDICT:
        """Convert the Center model instance to a CenterShallowDataDict.

        Returns:
            CenterShallowDataDict: The converted data dictionary.
        """
        data_dict = self._to_ddict()
        # TODO handle uuids of related examination, patient, ....
        ddict = self.ddict_shallow(**data_dict)
        return ddict
