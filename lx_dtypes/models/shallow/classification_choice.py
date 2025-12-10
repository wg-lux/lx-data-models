from lx_dtypes.utils.factories.field_defaults import list_of_str_factory
from lx_dtypes.utils.mixins import BaseModelMixin


class ClassificationChoiceShallow(BaseModelMixin):
    """Model representing a classification choice."""

    classification_choice_descriptor_names: list[str] = (
        list_of_str_factory()
    )  # List of classification choice descriptor names
    type_names: list[str] = list_of_str_factory()  # List of classification type names
