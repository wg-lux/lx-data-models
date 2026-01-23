from typing import List

from pydantic import Field

from lx_dtypes.models.base.app_base_model.pydantic.LedgerBaseModel import (
    LedgerBaseModel,
)
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
from lx_dtypes.serialization import parse_str_list

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
        descriptor_value: str | int | float | bool | List[str],
    ) -> PFindingClassificationChoiceDescriptor:
        if descriptor.is_numeric:
            descriptor_value = float(descriptor_value)  # type: ignore
        elif descriptor.is_boolean:
            # Explicit parsing to avoid bool("false") == True
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
                descriptor_value = bool(descriptor_value)  # type: ignore
        elif descriptor.is_selection:
            # Ensure descriptor_value is a list of strings; avoid list() on raw strings
            if isinstance(descriptor_value, list):
                # Assume already a list of strings
                pass
            elif isinstance(descriptor_value, str):
                descriptor_value = parse_str_list(descriptor_value)  # type: ignore[assignment]
            else:
                # Wrap other scalar values as a single string element
                descriptor_value = [str(descriptor_value)]  # type: ignore[assignment]
        elif descriptor.is_text:
            descriptor_value = str(descriptor_value)  # type: ignore
        else:
            raise ValueError(
                f"Unsupported descriptor type for descriptor {descriptor.name}"
            )

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
