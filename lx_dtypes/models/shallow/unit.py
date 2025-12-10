from typing import List, Optional

from pydantic import Field

from lx_dtypes.utils.factories.field_defaults import list_of_str_factory
from lx_dtypes.utils.mixins.base_model import BaseModelMixin
from lx_dtypes.utils.mixins.tags import TaggedMixin


class UnitTypeShallow(BaseModelMixin, TaggedMixin):
    pass


class UnitShallow(BaseModelMixin):
    """Model representing a medical intervention."""

    abbreviation: Optional[str] = None
    type_names: List[str] = Field(default_factory=list_of_str_factory)
