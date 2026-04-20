from typing import List, Union

from lx_dtypes.models.base.app_base_model.pydantic.LedgerBaseModel import (
    LedgerBaseModel,
)
from lx_dtypes.names import (
    P_INDICATION_CLASSIFICATION_DESCRIPTOR_MODEL_LIST_TYPE_FIELDS,
    P_INDICATION_CLASSIFICATION_DESCRIPTOR_MODEL_NESTED_FIELDS,
)

from .DataDict import PIndicationClassificationDescriptorDataDict


class PIndicationClassificationDescriptor(
    LedgerBaseModel[PIndicationClassificationDescriptorDataDict]
):
    descriptor_value: Union[str, int, float, bool, List[str]]
    classification_choice_descriptor: str
    patient_indication_classification: str

    @classmethod
    def list_type_fields(cls) -> List[str]:
        return P_INDICATION_CLASSIFICATION_DESCRIPTOR_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[PIndicationClassificationDescriptorDataDict]:
        return PIndicationClassificationDescriptorDataDict

    @classmethod
    def nested_fields(cls) -> List[str]:
        return P_INDICATION_CLASSIFICATION_DESCRIPTOR_MODEL_NESTED_FIELDS
