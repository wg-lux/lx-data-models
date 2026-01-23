from typing import List

from lx_dtypes.models.base.app_base_model.pydantic.LedgerBaseModel import (
    LedgerBaseModel,
)
from lx_dtypes.names import (
    P_INDICATION_MODEL_LIST_TYPE_FIELDS,
    P_INDICATION_MODEL_NESTED_FIELDS,
)

from .DataDict import (
    PIndicationDataDict,
)


class PIndication(LedgerBaseModel[PIndicationDataDict]):
    indication: str
    patient_examination: str

    @classmethod
    def list_type_fields(cls) -> List[str]:
        return P_INDICATION_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[PIndicationDataDict]:
        return PIndicationDataDict

    @classmethod
    def nested_fields(cls) -> List[str]:
        return P_INDICATION_MODEL_NESTED_FIELDS
