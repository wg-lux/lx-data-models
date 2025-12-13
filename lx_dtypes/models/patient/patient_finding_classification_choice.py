from typing import Any, Dict, List, Optional, Union

from pydantic import Field, field_serializer

from lx_dtypes.utils.factories.field_defaults import (
    list_of_patient_finding_classification_choice_descriptor_factory,
    uuid_factory,
)
from lx_dtypes.utils.mixins.base_model import AppBaseModel

from .patient_classification_choice_descriptor import (
    PatientFindingClassificationChoiceDescriptor,
)


class PatientFindingClassificationChoice(AppBaseModel):
    uuid: str = Field(default_factory=uuid_factory)
    name: str
    patient_uuid: str
    patient_examination_uuid: Optional[str] = None
    patient_finding_uuid: str
    patient_finding_classifications_uuid: str
    classification_name: str
    descriptors: List[PatientFindingClassificationChoiceDescriptor] = Field(
        default_factory=list_of_patient_finding_classification_choice_descriptor_factory
    )

    @field_serializer("descriptors")
    def serialize_descriptors(
        self, descriptors: List[PatientFindingClassificationChoiceDescriptor]
    ) -> List[Dict[str, Any]]:
        return [descriptor.model_dump() for descriptor in descriptors]

    @classmethod
    def create(
        cls,
        choice_name: str,
        patient_uuid: str,
        patient_finding_uuid: str,
        patient_examination_uuid: Optional[str],
        patient_finding_classifications_uuid: str,
        classification_name: str,
    ) -> "PatientFindingClassificationChoice":
        """Factory method to create a PatientFindingClassificationChoice instance.

        Args:
            patient_uuid (str): The UUID of the patient.
            patient_finding_uuid (str): The UUID of the patient finding.
            patient_examination_uuid (Optional[str]): The UUID of the patient examination.
            patient_finding_classifications_uuid (str): The UUID of the patient finding classifications.
            classification_name (str): The name of the classification.

        Returns:
            PatientFindingClassificationChoice: The created PatientFindingClassificationChoice instance.
        """
        model_dict: Dict[
            str,
            Union[
                str, Optional[str], List[PatientFindingClassificationChoiceDescriptor]
            ],
        ] = {
            "name": choice_name,
            "patient_uuid": patient_uuid,
            "patient_examination_uuid": patient_examination_uuid,
            "patient_finding_uuid": patient_finding_uuid,
            "patient_finding_classifications_uuid": patient_finding_classifications_uuid,
            "classification_name": classification_name,
            "descriptors": [],
        }
        instance = cls.model_validate(model_dict)
        return instance

    def get_descriptor_by_uuid(
        self, descriptor_uuid: str
    ) -> PatientFindingClassificationChoiceDescriptor:
        for descriptor in self.descriptors:
            if descriptor.uuid == descriptor_uuid:
                return descriptor
        raise ValueError(f"Descriptor with UUID '{descriptor_uuid}' not found.")
