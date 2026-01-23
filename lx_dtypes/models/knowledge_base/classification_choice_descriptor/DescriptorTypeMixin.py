from pydantic import BaseModel, Field

from lx_dtypes.names import ClassificationChoiceDescriptorTypes


class DescriptorTypeMixin(BaseModel):
    classification_choice_descriptor_type: ClassificationChoiceDescriptorTypes = Field(
        default_factory=lambda: ClassificationChoiceDescriptorTypes.NUMERIC
    )

    @property
    def is_numeric(self) -> bool:
        """
        Indicates whether the classification_choice_descriptor_type is numeric.

        Returns:
            True if the descriptor type equals ClassificationChoiceDescriptorTypes.NUMERIC, False otherwise.
        """
        return (
            self.classification_choice_descriptor_type
            == ClassificationChoiceDescriptorTypes.NUMERIC
        )

    @property
    def is_selection(self) -> bool:
        """
        Determine whether the descriptor's classification type is selection.

        Returns:
            `true` if `classification_choice_descriptor_type` equals `ClassificationChoiceDescriptorTypes.SELECTION`, `false` otherwise.
        """
        return (
            self.classification_choice_descriptor_type
            == ClassificationChoiceDescriptorTypes.SELECTION
        )

    @property
    def is_boolean(self) -> bool:
        """
        Return whether the descriptor's classification choice type is boolean.

        Returns:
            True if the descriptor's `classification_choice_descriptor_type` equals ClassificationChoiceDescriptorTypes.BOOLEAN, False otherwise.
        """
        return (
            self.classification_choice_descriptor_type
            == ClassificationChoiceDescriptorTypes.BOOLEAN
        )

    @property
    def is_text(self) -> bool:
        """
        Indicates whether the descriptor type is text.

        Returns:
            `True` if `classification_choice_descriptor_type` equals `ClassificationChoiceDescriptorTypes.TEXT`, `False` otherwise.
        """
        return (
            self.classification_choice_descriptor_type
            == ClassificationChoiceDescriptorTypes.TEXT
        )
