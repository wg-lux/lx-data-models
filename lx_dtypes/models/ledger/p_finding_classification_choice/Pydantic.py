from typing import List

from pydantic import Field

from lx_dtypes.models.base.app_base_model.pydantic.LedgerBaseModel import (
    LedgerBaseModel,
)
from lx_dtypes.models.descriptor_value import DescriptorValue
from lx_dtypes.models.knowledge_base.classification_choice_descriptor.ClassificationChoiceDescriptor import (
    ClassificationChoiceDescriptor,
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
    SerializedPFindingClassificationChoiceDataDict,
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

    def create_descriptor(
        self,
        descriptor: "ClassificationChoiceDescriptor",
        descriptor_value: DescriptorValue,
    ) -> PFindingClassificationChoiceDescriptor:
        descriptor_value = descriptor.normalize_value(descriptor_value)

        p_descriptor = PFindingClassificationChoiceDescriptor(
            classification_choice_descriptor=descriptor.name,
            descriptor_value=descriptor_value,
            patient_finding_classification_choice=str(self.uuid),
        )

        self.patient_finding_classification_choice_descriptors.append(p_descriptor)
        return p_descriptor

    @property
    def serialized_ddict_class(
        self,
    ) -> type[SerializedPFindingClassificationChoiceDataDict]:
        return SerializedPFindingClassificationChoiceDataDict

    @classmethod
    def serialized_model_class(cls) -> type["SerializedPFindingClassificationChoice"]:
        return SerializedPFindingClassificationChoice


class SerializedPFindingClassificationChoice(
    LedgerBaseModel[SerializedPFindingClassificationChoiceDataDict]
):
    classification: str
    classification_choice: str
    patient_finding_classifications: str
    patient_finding_classification_choice_descriptors: str = ""

    @classmethod
    def list_type_fields(cls) -> List[str]:
        return P_FINDING_CLASSIFICATION_CHOICE_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[SerializedPFindingClassificationChoiceDataDict]:
        return SerializedPFindingClassificationChoiceDataDict

    @classmethod
    def nested_fields(cls) -> List[str]:
        return []
