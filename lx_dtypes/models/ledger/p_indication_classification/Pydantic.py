from typing import List

from pydantic import Field

from lx_dtypes.models.base.app_base_model.pydantic.LedgerBaseModel import (
    LedgerBaseModel,
)
from lx_dtypes.models.descriptor_value import DescriptorValue
from lx_dtypes.models.knowledge_base.classification_choice_descriptor.ClassificationChoiceDescriptor import (
    ClassificationChoiceDescriptor,
)
from lx_dtypes.models.ledger.p_indication_classification_descriptor.Pydantic import (
    PIndicationClassificationDescriptor,
)
from lx_dtypes.names import (
    P_INDICATION_CLASSIFICATION_MODEL_LIST_TYPE_FIELDS,
    P_INDICATION_CLASSIFICATION_MODEL_NESTED_FIELDS,
)

from .DataDict import (
    PIndicationClassificationDataDict,
    SerializedPIndicationClassificationDataDict,
)


class PIndicationClassification(LedgerBaseModel[PIndicationClassificationDataDict]):
    classification: str
    classification_choice: str
    patient_indication: str
    patient_indication_classification_descriptors: List[
        PIndicationClassificationDescriptor
    ] = Field(default_factory=list)

    @classmethod
    def list_type_fields(cls) -> List[str]:
        return P_INDICATION_CLASSIFICATION_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[PIndicationClassificationDataDict]:
        return PIndicationClassificationDataDict

    @classmethod
    def nested_fields(cls) -> List[str]:
        return P_INDICATION_CLASSIFICATION_MODEL_NESTED_FIELDS

    def create_descriptor(
        self,
        descriptor: "ClassificationChoiceDescriptor",
        descriptor_value: DescriptorValue,
    ) -> PIndicationClassificationDescriptor:
        descriptor_value = descriptor.normalize_value(descriptor_value)

        p_descriptor = PIndicationClassificationDescriptor(
            classification_choice_descriptor=descriptor.name,
            descriptor_value=descriptor_value,
            patient_indication_classification=str(self.uuid),
        )
        self.patient_indication_classification_descriptors.append(p_descriptor)
        return p_descriptor

    @property
    def serialized_ddict_class(
        self,
    ) -> type[SerializedPIndicationClassificationDataDict]:
        return SerializedPIndicationClassificationDataDict

    @classmethod
    def serialized_model_class(cls) -> type["SerializedPIndicationClassification"]:
        return SerializedPIndicationClassification


class SerializedPIndicationClassification(
    LedgerBaseModel[SerializedPIndicationClassificationDataDict]
):
    classification: str
    classification_choice: str
    patient_indication: str
    patient_indication_classification_descriptors: str = ""

    @classmethod
    def list_type_fields(cls) -> List[str]:
        return P_INDICATION_CLASSIFICATION_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[SerializedPIndicationClassificationDataDict]:
        return SerializedPIndicationClassificationDataDict

    @classmethod
    def nested_fields(cls) -> List[str]:
        return []
