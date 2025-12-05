from typing import List

from pydantic import Field

from lx_dtypes.utils.factories.field_defaults import list_of_str_factory
from lx_dtypes.utils.mixins.base_model import BaseModelMixin
from lx_dtypes.utils.mixins.tags import TaggedMixin


class ClassificationTypeShallow(BaseModelMixin, TaggedMixin):
    pass


class ClassificationShallow(BaseModelMixin, TaggedMixin):
    """
    Model representing a classification using only shallow references:
    - classification_choices is a list of classification choice IDs (names as str)
    - types is a list of classification type IDs (names as str)
    """

    classification_choices: List[str] = Field(default_factory=list_of_str_factory)
    types: List[str] = Field(default_factory=list_of_str_factory)
