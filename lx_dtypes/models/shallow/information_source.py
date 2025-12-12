from typing import List

from pydantic import Field

from lx_dtypes.utils.factories.field_defaults import list_of_str_factory
from lx_dtypes.utils.mixins.base_model import BaseModelMixin
from lx_dtypes.utils.mixins.tags import TaggedMixin


class InformationSourceTypeShallow(BaseModelMixin, TaggedMixin):
    """Simple container for information source type metadata."""


class InformationSourceShallow(BaseModelMixin, TaggedMixin):
    """
    Shallow Model representing an information source.

    Attributes:
        name (str): The name of the classification choice.
        name_de (str | None): The German name of the classification choice.
        name_en (str | None): The English name of the classification choice.
        description (str | None): The description of the classification choice.
        types (list[str]): Names of associated information source types.
    """

    types: List[str] = Field(default_factory=list_of_str_factory)
