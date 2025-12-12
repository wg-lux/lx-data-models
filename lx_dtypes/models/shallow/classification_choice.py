from lx_dtypes.utils.factories.field_defaults import list_of_str_factory
from lx_dtypes.utils.mixins import BaseModelMixin


class ClassificationChoiceShallow(BaseModelMixin):
    """
    Shallow reference to descriptors and types used by a classification choice.
    Inherits from BaseModelMixin for common model functionality.

    Attributes:
        name (str): The name of the classification choice.
        name_de (str | None): The German name of the classification choice.
        name_en (str | None): The English name of the classification choice.
        description (str | None): The description of the classification choice.
        classification_choice_descriptor_names (list[str]): Names of associated descriptors.
        type_names (list[str]): Names of associated classification choice types.

    """

    classification_choice_descriptor_names: list[str] = list_of_str_factory()
    type_names: list[str] = list_of_str_factory()
