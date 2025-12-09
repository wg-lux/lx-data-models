from typing import Dict, List, Optional, Union

from pydantic import Field

from lx_dtypes.utils.factories.field_defaults import (
    list_of_patient_finding_classifications_factory,
    uuid_factory,
)
from lx_dtypes.utils.mixins.base_model import AppBaseModel

from .patient_finding_classifications import PatientFindingClassifications


class PatientFinding(AppBaseModel):
    uuid: str = Field(default_factory=uuid_factory)
    patient_uuid: str
    patient_examination_uuid: Optional[str] = None
    finding_name: str
    classifications: List[PatientFindingClassifications] = Field(
        default_factory=list_of_patient_finding_classifications_factory
    )

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
            "classifications": [],
        }
        instance = cls.model_validate(model_dict)
        return instance
