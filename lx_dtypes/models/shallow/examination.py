from typing import List

from pydantic import Field

from lx_dtypes.utils.factories.field_defaults import list_of_str_factory
from lx_dtypes.utils.mixins.base_model import BaseModelMixin
from lx_dtypes.utils.mixins.tags import TaggedMixin


class ExaminationTypeShallow(BaseModelMixin, TaggedMixin):
    pass


class ExaminationShallow(BaseModelMixin, TaggedMixin):
    """
    Model representing an examination using only shallow references:
    - findings is a list of finding IDs (names as str)
    - types is a list of examination type IDs (names as str)
    - indications is a list of indication IDs (names as str)
    """

    finding_names: List[str] = Field(default_factory=list_of_str_factory)
    type_names: List[str] = Field(default_factory=list_of_str_factory)
    indication_names: List[str] = Field(default_factory=list_of_str_factory)
