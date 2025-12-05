from typing import List

from pydantic import Field

from lx_dtypes.utils.factories.field_defaults import list_of_str_factory
from lx_dtypes.utils.mixins.base_model import BaseModelMixin
from lx_dtypes.utils.mixins.tags import TaggedMixin


class FindingTypeShallow(BaseModelMixin, TaggedMixin):
    pass


class FindingShallow(BaseModelMixin, TaggedMixin):
    """
    Model representing a finding using only shallow references:
    - classifications is a list of of classification IDs (names as str)
    - types is a list of finding type IDs (names as str)
    """

    classifications: List[str] = Field(default_factory=list_of_str_factory)
    types: List[str] = Field(default_factory=list_of_str_factory)
