from typing import List

from lx_dtypes.models.base.app_base_model.pydantic.LedgerBaseModel import (
    LedgerBaseModel,
)
from lx_dtypes.names import (
    P_FINDING_MODEL_LIST_TYPE_FIELDS,
    P_FINDING_MODEL_NESTED_FIELDS,
)

from .DataDict import (
    PFindingDataDict,
)


class PFinding(LedgerBaseModel[PFindingDataDict]):
    finding: str
    patient_examination: str

    @classmethod
    def list_type_fields(cls) -> List[str]:
        return P_FINDING_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[PFindingDataDict]:
        return PFindingDataDict

    @classmethod
    def nested_fields(cls) -> List[str]:
        return P_FINDING_MODEL_NESTED_FIELDS
