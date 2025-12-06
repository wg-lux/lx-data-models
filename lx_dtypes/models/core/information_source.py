from typing import Dict

from pydantic import Field

from lx_dtypes.utils.factories.field_defaults import information_source_type_by_name_factory
from lx_dtypes.utils.mixins.base_model import BaseModelMixin
from lx_dtypes.utils.mixins.tags import TaggedMixin


class InformationSourceType(BaseModelMixin, TaggedMixin):
    pass


class InformationSource(BaseModelMixin, TaggedMixin):
    """
    Model representing an indication using only shallow references:
    - types is a list of indication type IDs (names as str)
    """

    types: Dict[str, InformationSourceType] = Field(default_factory=information_source_type_by_name_factory)
