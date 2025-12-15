from typing import Dict, List, NotRequired, Optional, TypedDict, Union

from pydantic import Field, field_serializer

from lx_dtypes.utils.factories.field_defaults import (
    list_of_patient_finding_classification_choice_descriptor_factory,
    list_of_str_factory,
    uuid_factory,
)
from lx_dtypes.utils.mixins.base_model import AppBaseModel

from .patient_classification_choice_descriptor import (
    PatientFindingClassificationChoiceDescriptor,
    PatientFindingClassificationChoiceDescriptorDataDict,
)


class PatientFindingClassificationChoiceShallowDataDict(TypedDict):
    uuid: str
    name: str
    patient_uuid: str
    patient_examination_uuid: Optional[str]
    patient_finding_uuid: str
    patient_finding_classifications_uuid: str
    classification_name: str
    descriptor_uuids: List[str]


class PatientFindingClassificationChoiceDataDict(TypedDict):
    descriptors: NotRequired[List[PatientFindingClassificationChoiceDescriptorDataDict]]


class PatientFindingClassificationChoiceShallow(AppBaseModel):
    uuid: str = Field(default_factory=uuid_factory)
    name: str
    patient_uuid: str
    patient_examination_uuid: Optional[str] = None
    patient_finding_uuid: str
    patient_finding_classifications_uuid: str
    classification_name: str
    descriptor_uuids: List[str] = Field(default_factory=list_of_str_factory)

    @property
    def ddict_shallow(self) -> type[PatientFindingClassificationChoiceShallowDataDict]:
        return PatientFindingClassificationChoiceShallowDataDict

    def to_ddict_shallow(self) -> PatientFindingClassificationChoiceShallowDataDict:
        data_dict = self.ddict_shallow(**self.model_dump(exclude_defaults=False))
        return data_dict


class PatientFindingClassificationChoice(PatientFindingClassificationChoiceShallow):
    descriptors: List[PatientFindingClassificationChoiceDescriptor] = Field(
        default_factory=list_of_patient_finding_classification_choice_descriptor_factory
    )

    @property
    def ddict(self) -> type[PatientFindingClassificationChoiceDataDict]:
        return PatientFindingClassificationChoiceDataDict

    def to_ddict(self) -> PatientFindingClassificationChoiceDataDict:
        data_dict = self.ddict(**self.model_dump())
        return data_dict

    def to_ddict_shallow(self) -> PatientFindingClassificationChoiceShallowDataDict:
        descriptor_uuids = [descriptor.uuid for descriptor in self.descriptors]
        data_dict = self.ddict_shallow(
            uuid=self.uuid,
            name=self.name,
            patient_uuid=self.patient_uuid,
            patient_examination_uuid=self.patient_examination_uuid,
            patient_finding_uuid=self.patient_finding_uuid,
            patient_finding_classifications_uuid=self.patient_finding_classifications_uuid,
            classification_name=self.classification_name,
            descriptor_uuids=descriptor_uuids,
        )
        return data_dict

    @field_serializer("descriptors")
    def serialize_descriptors(
        self, descriptors: List[PatientFindingClassificationChoiceDescriptor]
    ) -> List[PatientFindingClassificationChoiceDescriptorDataDict]:
        return [descriptor.to_ddict() for descriptor in descriptors]

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
