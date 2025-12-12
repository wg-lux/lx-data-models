from typing import List, Optional

from pydantic import Field

from lx_dtypes.utils.factories.field_defaults import list_of_str_factory
from lx_dtypes.utils.mixins.base_model import BaseModelMixin
from lx_dtypes.utils.mixins.tags import TaggedMixin


class UnitTypeShallow(BaseModelMixin, TaggedMixin):
    """Taggable metadata container for unit types."""


class UnitShallow(BaseModelMixin):
    """
    Shallow model representing a measurement unit.
    Attributes:
        name (str): The name of the classification choice.
        name_de (str | None): The German name of the classification choice.
        name_en (str | None): The English name of the classification choice.
        description (str | None): The description of the classification choice.
        abbreviation (str | None): The abbreviation of the unit.
        type_names (list[str]): Names of associated unit types.
    """

    abbreviation: Optional[str] = None
    type_names: List[str] = Field(default_factory=list_of_str_factory)
