from typing import List, NotRequired, Optional, TypedDict, Union

from pydantic import Field, field_serializer

from lx_dtypes.models.core.classification_choice_descriptor import (
    ClassificationChoiceDescriptor,
)
from lx_dtypes.models.shallow.classification_choice_descriptor import (
    ClassificationChoiceDescriptorShallowDataDict,
)
from lx_dtypes.utils.factories.field_defaults import uuid_factory
from lx_dtypes.utils.mixins.base_model import AppBaseModel


class PatientFindingClassificationChoiceDescriptorDataDict(TypedDict):
    uuid: NotRequired[str]
    patient_uuid: str
    patient_examination_uuid: Optional[str]
    patient_finding_uuid: str
    patient_finding_classifications_uuid: str
    patient_finding_classification_choice_uuid: str
    descriptor_value: Union[str, int, float, bool, List[str]]
    descriptor: ClassificationChoiceDescriptorShallowDataDict


class PatientFindingClassificationChoiceDescriptorShallowDataDict(TypedDict):
    uuid: str
    patient_uuid: str
    patient_examination_uuid: Optional[str]
    patient_finding_uuid: str
    patient_finding_classifications_uuid: str
    patient_finding_classification_choice_uuid: str
    descriptor_value: Union[str, int, float, bool, List[str]]
    descriptor_name: str


class PatientFindingClassificationChoiceDescriptorShallow(AppBaseModel):
    uuid: str = Field(default_factory=uuid_factory)
    descriptor_value: Union[str, int, float, bool, List[str]]
    patient_uuid: str
    patient_examination_uuid: Optional[str] = None
    patient_finding_uuid: str
    patient_finding_classifications_uuid: str
    patient_finding_classification_choice_uuid: str
    descriptor_name: str

    @property
    def ddict_shallow(
        self,
    ) -> type[PatientFindingClassificationChoiceDescriptorShallowDataDict]:
        return PatientFindingClassificationChoiceDescriptorShallowDataDict

    def to_ddict_shallow(
        self,
    ) -> PatientFindingClassificationChoiceDescriptorShallowDataDict:
        data_dict = self.ddict_shallow(**self.model_dump())
        return data_dict


class PatientFindingClassificationChoiceDescriptor(
    PatientFindingClassificationChoiceDescriptorShallow
):
    descriptor: Optional[ClassificationChoiceDescriptor] = None

    @property
    def ddict(self) -> type[PatientFindingClassificationChoiceDescriptorDataDict]:
        return PatientFindingClassificationChoiceDescriptorDataDict

    @field_serializer("descriptor")
    def serialize_descriptor(
        self, descriptor: ClassificationChoiceDescriptor
    ) -> ClassificationChoiceDescriptorShallowDataDict:
        return descriptor.to_ddict_shallow()

    def to_ddict(self) -> PatientFindingClassificationChoiceDescriptorDataDict:
        data_dict = self.ddict(**self.model_dump())
        return data_dict

    def to_ddict_shallow(
        self,
    ) -> PatientFindingClassificationChoiceDescriptorShallowDataDict:
        data_dict = self.ddict_shallow(**self.model_dump())
        return data_dict
