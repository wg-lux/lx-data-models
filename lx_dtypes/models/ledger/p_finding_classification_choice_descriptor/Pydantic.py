from typing import List, Union

from lx_dtypes.models.base.app_base_model.pydantic.LedgerBaseModel import (
    LedgerBaseModel,
)
from lx_dtypes.names import (
    P_FINDING_CLASSIFICATION_CHOICE_DESCRIPTOR_MODEL_LIST_TYPE_FIELDS,
    P_FINDING_CLASSIFICATION_CHOICE_DESCRIPTOR_MODEL_NESTED_FIELDS,
)

from .DataDict import PFindingClassificationChoiceDescriptorDataDict


class PFindingClassificationChoiceDescriptor(
    LedgerBaseModel[PFindingClassificationChoiceDescriptorDataDict]
):
    descriptor_value: Union[str, int, float, bool, List[str]]
    classification_choice_descriptor: str
    patient_finding_classification_choice: str

    @classmethod
    def list_type_fields(cls) -> List[str]:
        return P_FINDING_CLASSIFICATION_CHOICE_DESCRIPTOR_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[PFindingClassificationChoiceDescriptorDataDict]:
        return PFindingClassificationChoiceDescriptorDataDict

    @classmethod
    def nested_fields(cls) -> List[str]:
        return P_FINDING_CLASSIFICATION_CHOICE_DESCRIPTOR_MODEL_NESTED_FIELDS
