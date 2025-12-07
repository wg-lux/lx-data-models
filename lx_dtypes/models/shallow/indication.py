from typing import List

from pydantic import Field

from lx_dtypes.utils.factories.field_defaults import list_of_str_factory
from lx_dtypes.utils.mixins.base_model import BaseModelMixin
from lx_dtypes.utils.mixins.tags import TaggedMixin


class IndicationTypeShallow(BaseModelMixin, TaggedMixin):
    pass


class IndicationShallow(BaseModelMixin, TaggedMixin):
    """
    Model representing an indication using only shallow references:
    - types is a list of indication type IDs (names as str)
    """

    type_names: List[str] = Field(default_factory=list_of_str_factory)
    expected_intervention_names: List[str] = Field(default_factory=list_of_str_factory)
