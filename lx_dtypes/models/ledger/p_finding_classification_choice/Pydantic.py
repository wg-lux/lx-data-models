from typing import List

from pydantic import Field

from lx_dtypes.models.base.app_base_model.pydantic.LedgerBaseModel import (
    LedgerBaseModel,
)
from lx_dtypes.models.ledger.p_finding_classification_choice_descriptor.Pydantic import (
    PFindingClassificationChoiceDescriptor,
)
from lx_dtypes.names import (
    P_FINDING_CLASSIFICATION_CHOICE_MODEL_LIST_TYPE_FIELDS,
    P_FINDING_CLASSIFICATION_CHOICE_MODEL_NESTED_FIELDS,
)

from .DataDict import (
    PFindingClassificationChoiceDataDict,
)


class PFindingClassificationChoice(
    LedgerBaseModel[PFindingClassificationChoiceDataDict]
):
    classification: str
    classification_choice: str
    patient_finding_classifications: str
    patient_finding_classification_choice_descriptors: List[
        PFindingClassificationChoiceDescriptor
    ] = Field(default_factory=list)

    @classmethod
    def list_type_fields(cls) -> List[str]:
        return P_FINDING_CLASSIFICATION_CHOICE_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[PFindingClassificationChoiceDataDict]:
        return PFindingClassificationChoiceDataDict

    @classmethod
    def nested_fields(cls) -> List[str]:
        return P_FINDING_CLASSIFICATION_CHOICE_MODEL_NESTED_FIELDS
