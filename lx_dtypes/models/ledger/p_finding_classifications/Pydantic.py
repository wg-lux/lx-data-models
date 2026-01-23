from typing import List

from pydantic import Field

from lx_dtypes.models.base.app_base_model.pydantic.LedgerBaseModel import (
    LedgerBaseModel,
)
from lx_dtypes.models.ledger.p_finding_classification_choice.Pydantic import (
    PFindingClassificationChoice,
)
from lx_dtypes.names import (
    P_FINDING_CLASSIFICATIONS_MODEL_LIST_TYPE_FIELDS,
    P_FINDING_CLASSIFICATIONS_MODEL_NESTED_FIELDS,
)

from .DataDict import (
    PFindingClassificationsDataDict,
    SerializedPFindingClassificationsDataDict,
)


class PFindingClassifications(LedgerBaseModel[PFindingClassificationsDataDict]):
    patient_finding: str
    patient_finding_classification_choices: List[PFindingClassificationChoice] = Field(
        default_factory=list
    )

    @classmethod
    def list_type_fields(cls) -> List[str]:
        return P_FINDING_CLASSIFICATIONS_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[PFindingClassificationsDataDict]:
        return PFindingClassificationsDataDict

    @classmethod
    def nested_fields(cls) -> List[str]:
        return P_FINDING_CLASSIFICATIONS_MODEL_NESTED_FIELDS

    @property
    def serialized_ddict_class(self) -> type[SerializedPFindingClassificationsDataDict]:
        return SerializedPFindingClassificationsDataDict

    @classmethod
    def serialized_model_class(cls) -> type["SerializedPFindingClassifications"]:
        return SerializedPFindingClassifications


class SerializedPFindingClassifications(
    LedgerBaseModel[SerializedPFindingClassificationsDataDict]
):
    patient_finding: str
    patient_finding_classification_choices: str = ""

    @classmethod
    def list_type_fields(cls) -> List[str]:
        return P_FINDING_CLASSIFICATIONS_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[SerializedPFindingClassificationsDataDict]:
        return SerializedPFindingClassificationsDataDict

    @classmethod
    def nested_fields(cls) -> List[str]:
        return []
