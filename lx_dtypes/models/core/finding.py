from typing import Dict, List

from pydantic import Field

from lx_dtypes.utils.factories.field_defaults import classification_by_name_factory, finding_type_by_name_factory, list_of_str_factory
from lx_dtypes.utils.mixins.base_model import BaseModelMixin
from lx_dtypes.utils.mixins.tags import TaggedMixin

from .classification import Classification


class FindingType(BaseModelMixin, TaggedMixin):
    """Model representing a finding type."""

    pass


class Finding(BaseModelMixin, TaggedMixin):
    """Model representing a finding classification."""

    classifications: Dict[str, Classification] = Field(default_factory=classification_by_name_factory)
    types: Dict[str, FindingType] = Field(default_factory=finding_type_by_name_factory)


class FindingShallow(BaseModelMixin, TaggedMixin):
    """
    Model representing a finding using only shallow references:
    - classifications is a list of of classification IDs (names as str)
    - types is a list of finding type IDs (names as str)
    """

    classifications: List[str] = Field(default_factory=list_of_str_factory)
    types: List[str] = Field(default_factory=list_of_str_factory)
