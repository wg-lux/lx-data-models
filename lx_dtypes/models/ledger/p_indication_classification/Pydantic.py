from typing import List

from pydantic import Field

from lx_dtypes.models.base.app_base_model.pydantic.LedgerBaseModel import (
    LedgerBaseModel,
)
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
from lx_dtypes.serialization import parse_str_list

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
        descriptor_value: str | int | float | bool | List[str],
    ) -> PIndicationClassificationDescriptor:
        if descriptor.is_numeric:
            if isinstance(descriptor_value, list):
                raise ValueError(
                    f"List value is not supported for numeric descriptor {descriptor.name}"
                )
            descriptor_value = float(descriptor_value)
        elif descriptor.is_boolean:
            if isinstance(descriptor_value, str):
                normalized = descriptor_value.strip().lower()
                if normalized in {"true", "1", "yes", "y", "on"}:
                    descriptor_value = True  # type: ignore[assignment]
                elif normalized in {"false", "0", "no", "n", "off"}:
                    descriptor_value = False  # type: ignore[assignment]
                else:
                    raise ValueError(
                        f"Unsupported boolean string value '{descriptor_value}' "
                        f"for descriptor {descriptor.name}"
                    )
            else:
                descriptor_value = bool(descriptor_value)  # type: ignore[assignment]
        elif descriptor.is_selection:
            if isinstance(descriptor_value, list):
                pass
            elif isinstance(descriptor_value, str):
                descriptor_value = parse_str_list(descriptor_value)  # type: ignore[assignment]
            else:
                descriptor_value = [str(descriptor_value)]  # type: ignore[assignment]
        elif descriptor.is_text:
            descriptor_value = str(descriptor_value)  # type: ignore[assignment]
        else:
            raise ValueError(
                f"Unsupported descriptor type for descriptor {descriptor.name}"
            )

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
