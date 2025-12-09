from typing import Dict, List, Optional, Union

from pydantic import Field

from lx_dtypes.models.patient.patient_finding_classification_choice import (
    PatientFindingClassificationChoice,
)
from lx_dtypes.utils.factories.field_defaults import (
    uuid_factory,
)
from lx_dtypes.utils.mixins.base_model import AppBaseModel

from .patient_finding_classifications import PatientFindingClassifications


class PatientFinding(AppBaseModel):
    uuid: str = Field(default_factory=uuid_factory)
    patient_uuid: str
    patient_examination_uuid: Optional[str] = None
    finding_name: str
    classifications: Optional[PatientFindingClassifications] = None

    @classmethod
    def create(
        cls,
        patient_uuid: str,
        finding_name: str,
        patient_examination_uuid: Optional[str] = None,
    ):
        """Factory method to create a PatientFinding instance.

        Args:
            patient_uuid (str): The UUID of the patient.
            finding_name (str): The name of the finding.
            patient_examination_uuid (Optional[str]): The UUID of the patient examination.

        Returns:
            PatientFinding: The created PatientFinding instance.
        """
        model_dict: Dict[
            str, Optional[Union[str, List[PatientFindingClassifications]]]
        ] = {
            "patient_uuid": patient_uuid,
            "finding_name": finding_name,
            "patient_examination_uuid": patient_examination_uuid,
        }
        instance = cls.model_validate(model_dict)
        _ = instance.get_or_create_classifications()
        return instance

    def get_or_create_classifications(self) -> PatientFindingClassifications:
        if self.classifications is None:
            self.classifications = PatientFindingClassifications(
                patient_uuid=self.patient_uuid,
                patient_examination_uuid=self.patient_examination_uuid,
                patient_finding_uuid=self.uuid,
                finding_name=self.finding_name,
            )
        return self.classifications

    def add_classification_choice(
        self, classification_choice: "PatientFindingClassificationChoice"
    ):
        classifications = self.get_or_create_classifications()

        assert (
            classification_choice.patient_finding_classifications_uuid
            == classifications.uuid
        )
        assert classification_choice.patient_finding_uuid == self.uuid
        assert classification_choice.patient_uuid == self.patient_uuid

        classifications.choices.append(classification_choice)
