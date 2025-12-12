from typing import List

from pydantic import Field

from lx_dtypes.utils.factories.field_defaults import list_of_str_factory
from lx_dtypes.utils.mixins.base_model import BaseModelMixin
from lx_dtypes.utils.mixins.tags import TaggedMixin


class IndicationTypeShallow(BaseModelMixin, TaggedMixin):
    """Taggable metadata container for indication types."""


class IndicationShallow(BaseModelMixin, TaggedMixin):
    """
    Shallow model representing a medical indication.

    Attributes:
        name (str): The name of the classification choice.
        name_de (str | None): The German name of the classification choice.
        name_en (str | None): The English name of the classification choice.
        description (str | None): The description of the classification choice.
        type_names (list[str]): Names of associated indication types.
        expected_intervention_names (list[str]): Names of expected interventions.

    """

    type_names: List[str] = Field(default_factory=list_of_str_factory)
    expected_intervention_names: List[str] = Field(default_factory=list_of_str_factory)
