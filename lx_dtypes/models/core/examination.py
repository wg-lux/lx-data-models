from typing import Dict, List

from pydantic import Field

from lx_dtypes.utils.factories.field_defaults import list_of_str_factory
from lx_dtypes.utils.mixins.base_model import BaseModelMixin
from lx_dtypes.utils.mixins.tags import TaggedMixin

from .finding import Finding
from .indication import Indication


class ExaminationType(BaseModelMixin, TaggedMixin):
    """Model representing an examination type."""

    pass


class Examination(BaseModelMixin, TaggedMixin):
    """Model representing a finding classification."""

    findings: Dict[str, "Finding"] = Field(default_factory=dict)
    types: Dict[str, ExaminationType] = Field(default_factory=dict)
    indications: Dict[str, "Indication"] = Field(default_factory=dict)


class ExaminationShallow(BaseModelMixin, TaggedMixin):
    """
    Model representing an examination using only shallow references:
    - findings is a list of finding IDs (names as str)
    - types is a list of examination type IDs (names as str)
    - indications is a list of indication IDs (names as str)
    """

    findings: List[str] = Field(default_factory=list_of_str_factory)
    types: List[str] = Field(default_factory=list_of_str_factory)
    indications: List[str] = Field(default_factory=list_of_str_factory)
