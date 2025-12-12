from typing import List

from pydantic import Field

from lx_dtypes.utils.factories.field_defaults import list_of_str_factory
from lx_dtypes.utils.mixins.base_model import BaseModelMixin
from lx_dtypes.utils.mixins.tags import TaggedMixin


class FindingTypeShallow(BaseModelMixin, TaggedMixin):
    """Metadata shell for finding types."""


class FindingShallow(BaseModelMixin, TaggedMixin):
    """
    Shallow model representing a medical finding.

    Attributes:
        name (str): The name of the classification choice.
        name_de (str | None): The German name of the classification choice.
        name_en (str | None): The English name of the classification choice.
        description (str | None): The description of the classification choice.
        classification_names (list[str]): Names of associated classifications.
        type_names (list[str]): Names of associated finding types.
        intervention_names (list[str]): Names of associated interventions.

    """

    classification_names: List[str] = Field(default_factory=list_of_str_factory)
    type_names: List[str] = Field(default_factory=list_of_str_factory)
    intervention_names: List[str] = Field(default_factory=list_of_str_factory)
