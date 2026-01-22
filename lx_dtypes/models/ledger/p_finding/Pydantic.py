from typing import List

from pydantic import Field

from lx_dtypes.models.base.app_base_model.pydantic.LedgerBaseModel import (
    LedgerBaseModel,
)
from lx_dtypes.models.ledger.p_finding_classifications.Pydantic import (
    PFindingClassifications,
)
from lx_dtypes.models.ledger.p_interventions.Pydantic import (
    PFindingInterventions,
)
from lx_dtypes.names import (
    P_FINDING_MODEL_LIST_TYPE_FIELDS,
    P_FINDING_MODEL_NESTED_FIELDS,
)

from .DataDict import (
    PFindingDataDict,
    SerializedPFindingDataDict,
)


class PFinding(LedgerBaseModel[PFindingDataDict]):
    finding: str
    patient_examination: str
    patient_finding_classifications: List[PFindingClassifications] = Field(
        default_factory=list
    )
    patient_finding_interventions: List[PFindingInterventions] = Field(
        default_factory=list
    )

    @property
    def latest_classifications_obj(self) -> PFindingClassifications:
        if not self.patient_finding_classifications:
            _classifications = PFindingClassifications(
                patient_finding=str(self.uuid),
            )
            self.patient_finding_classifications.append(_classifications)
        # Assuming the last one is the latest based on some criteria
        classifications_list = self.patient_finding_classifications
        # Sort by creation time or any other criteria if available
        classifications_list.sort(key=lambda x: x.created_at)

        return classifications_list[-1]

    @classmethod
    def list_type_fields(cls) -> List[str]:
        return P_FINDING_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[PFindingDataDict]:
        return PFindingDataDict

    @classmethod
    def nested_fields(cls) -> List[str]:
        return P_FINDING_MODEL_NESTED_FIELDS

    @property
    def serialized_ddict_class(self) -> type[SerializedPFindingDataDict]:
        return SerializedPFindingDataDict

    @classmethod
    def serialized_model_class(cls) -> type["SerializedPFinding"]:
        return SerializedPFinding

    def get_p_classifications_by_uuid(
        self, classifications_uuid: str
    ) -> PFindingClassifications:
        for classifications in self.patient_finding_classifications:
            if str(classifications.uuid) == classifications_uuid:
                return classifications
        raise KeyError(
            f"Finding Classifications with UUID {classifications_uuid} not found in this finding."
        )


class SerializedPFinding(LedgerBaseModel[SerializedPFindingDataDict]):
    finding: str
    patient_examination: str
    patient_finding_classifications: str = ""
    patient_finding_interventions: str = ""

    @classmethod
    def list_type_fields(cls) -> List[str]:
        return P_FINDING_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[SerializedPFindingDataDict]:
        return SerializedPFindingDataDict

    @classmethod
    def nested_fields(cls) -> List[str]:
        return []
