import math

from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.descriptor_value import DescriptorValue
from lx_dtypes.models.knowledge_base.classification_choice_descriptor.BooleanDescriptorMixin import (
    BooleanDescriptorMixin,
)
from lx_dtypes.models.knowledge_base.classification_choice_descriptor.NumericDescriptorMixin import (
    NumericDescriptorMixin,
)
from lx_dtypes.models.knowledge_base.classification_choice_descriptor.SelectionDescriptorMixin import (
    SelectionDescriptorMixin,
)
from lx_dtypes.models.knowledge_base.classification_choice_descriptor.TextDescriptorMixin import (
    TextDescriptorMixin,
)
from lx_dtypes.models.knowledge_base.classification_choice_descriptor.UnitMixin import (
    UnitMixin,
)
from lx_dtypes.names import (
    CLASSIFICATION_CHOICE_DESCRIPTOR_MODEL_LIST_TYPE_FIELDS,
)
from lx_dtypes.serialization import parse_str_list

from .ClassificationChoiceDescriptorDataDict import (
    ClassificationChoiceDescriptorDataDict,
)


class ClassificationChoiceDescriptor(
    KnowledgebaseBaseModel[ClassificationChoiceDescriptorDataDict],
    NumericDescriptorMixin,
    SelectionDescriptorMixin,
    BooleanDescriptorMixin,
    UnitMixin,
    TextDescriptorMixin,
):
    """
    Model for classification choice descriptors in a knowledge base."""

    name: str

    @classmethod
    def list_type_fields(cls) -> list[str]:
        """
        Get the model's list-type field names.

        Returns:
            A list of field names that are treated as list-type fields for this classification choice descriptor.
        """
        return CLASSIFICATION_CHOICE_DESCRIPTOR_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[ClassificationChoiceDescriptorDataDict]:
        """
        Return the data-dictionary class associated with this descriptor.

        Returns:
            ddict_class (type[ClassificationChoiceDescriptorDataDict]): The class used to represent this descriptor's data dictionary.
        """
        return ClassificationChoiceDescriptorDataDict

    def validate_value(self, value: DescriptorValue) -> DescriptorValue:
        """Validate an observed value without coercion using this KB definition."""
        if self.is_numeric:
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or (isinstance(value, float) and not math.isfinite(value))
                or not self.numeric_min <= value <= self.numeric_max
            ):
                raise ValueError("Descriptor requires a finite number within KB bounds")
        elif self.is_boolean:
            if not isinstance(value, bool):
                raise ValueError("Descriptor requires a boolean")
        elif self.is_text:
            if not isinstance(value, str) or len(value) > self.text_max_length:
                raise ValueError("Descriptor requires text within KB maximum length")
        elif self.is_selection:
            if not isinstance(value, list) or not all(
                isinstance(item, str) for item in value
            ):
                raise ValueError("Descriptor requires a list of selection names")
            if len(set(value)) != len(value) or not set(value).issubset(
                self.selection_options
            ):
                raise ValueError("Unknown or repeated descriptor selection")
            if (not self.selection_multiple and len(value) != 1) or (
                self.selection_multiple
                and not self.selection_multiple_n_min
                <= len(value)
                <= self.selection_multiple_n_max
            ):
                raise ValueError("Descriptor selection cardinality is invalid")
        else:
            raise ValueError("Unsupported descriptor type")
        return value

    def normalize_value(self, value: DescriptorValue) -> DescriptorValue:
        """Normalize a ledger value according to this descriptor's type.

        Keeping this conversion on the knowledge-base descriptor ensures that
        finding and indication ledger records interpret identical descriptor
        definitions in the same way.
        """

        if self.is_numeric:
            if isinstance(value, list):
                raise ValueError(
                    f"List value is not supported for numeric descriptor {self.name}"
                )
            return float(value)

        if self.is_boolean:
            if isinstance(value, list):
                raise ValueError(
                    f"List value is not supported for boolean descriptor {self.name}"
                )
            if isinstance(value, str):
                normalized = value.strip().lower()
                if normalized in {"true", "1", "yes", "y", "on"}:
                    return True
                if normalized in {"false", "0", "no", "n", "off"}:
                    return False
                raise ValueError(
                    f"Unsupported boolean string value '{value}' "
                    f"for descriptor {self.name}"
                )
            return bool(value)

        if self.is_selection:
            if isinstance(value, (str, list)):
                return parse_str_list(value)
            return [str(value)]

        if self.is_text:
            return str(value)

        raise ValueError(f"Unsupported descriptor type for descriptor {self.name}")
