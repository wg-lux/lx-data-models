from typing import Dict, List

from lx_dtypes.utils.factories.field_defaults import indication_type_by_name_factory, list_of_str_factory
from pydantic import Field

from lx_dtypes.utils.mixins.base_model import BaseModelMixin
from lx_dtypes.utils.mixins.tags import TaggedMixin


class IndicationType(BaseModelMixin, TaggedMixin):
    """Model representing an indication type."""

    pass


class Indication(BaseModelMixin, TaggedMixin):
    """Model representing an indication."""

    types: Dict[str, IndicationType] = Field(default_factory=indication_type_by_name_factory)


class IndicationShallow(BaseModelMixin, TaggedMixin):
    """
    Model representing an indication using only shallow references:
    - types is a list of indication type IDs (names as str)
    """

    types: List[str] = Field(default_factory=list_of_str_factory)
