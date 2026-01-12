from pydantic import BaseModel, Field

from lx_dtypes.names import ClassificationChoiceDescriptorTypes


class DescriptorTypeMixin(BaseModel):
    classification_choice_descriptor_type: ClassificationChoiceDescriptorTypes = Field(
        default_factory=lambda: ClassificationChoiceDescriptorTypes.NUMERIC
    )

    @property
    def is_numeric(self) -> bool:
        return (
            self.classification_choice_descriptor_type
            == ClassificationChoiceDescriptorTypes.NUMERIC
        )

    @property
    def is_selection(self) -> bool:
        return (
            self.classification_choice_descriptor_type
            == ClassificationChoiceDescriptorTypes.SELECTION
        )

    @property
    def is_boolean(self) -> bool:
        return (
            self.classification_choice_descriptor_type
            == ClassificationChoiceDescriptorTypes.BOOLEAN
        )

    @property
    def is_text(self) -> bool:
        return (
            self.classification_choice_descriptor_type
            == ClassificationChoiceDescriptorTypes.TEXT
        )
