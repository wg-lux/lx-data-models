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
        """
        Return the most recent PFindingClassifications for this finding, creating and appending a new default classification if none exist.

        Returns:
            PFindingClassifications: The classification object with the latest `created_at` timestamp.
        """
        if not self.patient_finding_classifications:
            _classifications = PFindingClassifications(
                patient_finding=str(self.uuid),
            )
            self.patient_finding_classifications.append(_classifications)

        return max(self.patient_finding_classifications, key=lambda x: x.created_at)

    @classmethod
    def list_type_fields(cls) -> List[str]:
        """
        Return the field names that should be treated as list types for this model.

        Returns:
            List[str]: Predefined list-type field names for PFinding models.
        """
        return P_FINDING_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[PFindingDataDict]:
        """
        Expose the PFinding data-dictionary type associated with this model.

        Returns:
            type[PFindingDataDict]: The PFindingDataDict class used to represent this model's underlying data dictionary.
        """
        return PFindingDataDict

    @classmethod
    def nested_fields(cls) -> List[str]:
        """
        List nested field names for the PFinding model.

        Returns:
            List[str]: Field names that represent nested model relations for PFinding.
        """
        return P_FINDING_MODEL_NESTED_FIELDS

    @property
    def serialized_ddict_class(self) -> type[SerializedPFindingDataDict]:
        """
        Get the data-dictionary class used for serialized PFinding values.

        Returns:
            The `SerializedPFindingDataDict` class.
        """
        return SerializedPFindingDataDict

    @classmethod
    def serialized_model_class(cls) -> type["SerializedPFinding"]:
        """
        Get the SerializedPFinding model class.

        Returns:
            type[SerializedPFinding]: The SerializedPFinding model type.
        """
        return SerializedPFinding

    def get_p_classifications_by_uuid(
        self, classifications_uuid: str
    ) -> PFindingClassifications:
        """
        Retrieve a patient finding classification from this PFinding by its UUID.

        Parameters:
            classifications_uuid (str): The UUID of the classification to find.

        Returns:
            PFindingClassifications: The classification with the matching UUID.

        Raises:
            KeyError: If no classification with the given UUID exists in this finding.
        """
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
        """
        Return the field names that should be treated as list types for this model.

        Returns:
            List[str]: Predefined list-type field names for PFinding models.
        """
        return P_FINDING_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[SerializedPFindingDataDict]:
        """
        Expose the data-dict class used to represent serialized PFinding records.

        Returns:
            The `SerializedPFindingDataDict` type for serialized PFinding data.
        """
        return SerializedPFindingDataDict

    @classmethod
    def nested_fields(cls) -> List[str]:
        """
        Return the names of fields that are treated as nested (complex) types by the model.

        Returns:
            list[str]: Field names considered nested.
        """
        return []
