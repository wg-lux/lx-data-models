from django.db import models

from lx_dtypes.models.ledger.center import CenterDataDict
from lx_dtypes.models.core.center_shallow import CenterShallowDataDict

from ..base_model.base_model import KnowledgeBaseModel
from ..typing import OptionalCharFieldType


class Center(KnowledgeBaseModel):
    examiner_uuids: OptionalCharFieldType = (
        models.CharField(  # TODO make foreign key to examiner model
            max_length=255, null=True, blank=True
        )
    )

    @property
    def ddict_shallow(self) -> type[CenterShallowDataDict]:
        return CenterShallowDataDict

    @property
    def ddict(self) -> type[CenterDataDict]:
        return CenterDataDict

    class Meta(KnowledgeBaseModel.Meta):
        pass

    def to_ddict_shallow(self) -> CenterShallowDataDict:
        """Convert the Center model instance to a CenterDataDict.

        Returns:
            CenterDataDict: The converted data dictionary.
        """
        data_dict = self._to_ddict()
        examiner_uuids = self.examiner_uuids
        if examiner_uuids:
            data_dict["examiner_uuids"] = self.str_list_to_list(examiner_uuids)
        else:
            data_dict["examiner_uuids"] = []
        ddict = self.ddict_shallow(**data_dict)
        return ddict
