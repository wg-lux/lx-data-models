from typing import List, Optional, Union

from pydantic import Field, field_serializer

from lx_dtypes.models.base_models.base_model import (
    LedgerBaseModel,
    LedgerBaseModelDataDict,
)
from lx_dtypes.models.core.classification_choice_descriptor import (
    ClassificationChoiceDescriptor,
    ClassificationChoiceDescriptorDataDict,
)
from lx_dtypes.models.core.classification_choice_descriptor_shallow import (
    ClassificationChoiceDescriptorShallowDataDict,
)
from lx_dtypes.utils.factories.field_defaults import uuid_factory


class PatientFindingClassificationChoiceDescriptorShallowDataDict(
    LedgerBaseModelDataDict
):
    patient_uuid: str
    patient_examination_uuid: str
    patient_finding_uuid: str
    patient_finding_classifications_uuid: str
    patient_finding_classification_choice_uuid: str
    descriptor_value: Union[str, int, float, bool, List[str]]
    descriptor_name: str


class PatientFindingClassificationChoiceDescriptorDataDict(
    PatientFindingClassificationChoiceDescriptorShallowDataDict
):
    descriptor: ClassificationChoiceDescriptorShallowDataDict


class PatientFindingClassificationChoiceDescriptorShallow(LedgerBaseModel):
    uuid: str = Field(default_factory=uuid_factory)
    descriptor_value: Union[str, int, float, bool, List[str]]
    patient_uuid: str
    patient_examination_uuid: str
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
        self, descriptor: Optional[ClassificationChoiceDescriptor]
    ) -> Optional[ClassificationChoiceDescriptorDataDict]:
        if descriptor is None:
            return None
        return descriptor.to_ddict()

    def to_ddict(self) -> PatientFindingClassificationChoiceDescriptorDataDict:
        data_dict = self.ddict(**self.model_dump())
        return data_dict

    def to_ddict_shallow(
        self,
    ) -> PatientFindingClassificationChoiceDescriptorShallowDataDict:
        dump = self.model_dump()
        descriptor_name = self.descriptor.name if self.descriptor is not None else ""
        dump["descriptor_name"] = descriptor_name
        shallow_data = {
            key: dump[key]
            for key in self.ddict_shallow.__annotations__.keys()
            if key in dump
        }
        return self.ddict_shallow(**shallow_data)
