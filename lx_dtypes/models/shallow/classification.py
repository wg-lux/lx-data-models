from typing import List

from pydantic import Field

from lx_dtypes.utils.factories.field_defaults import list_of_str_factory
from lx_dtypes.utils.mixins.base_model import BaseModelMixin
from lx_dtypes.utils.mixins.tags import TaggedMixin


class ClassificationTypeShallow(BaseModelMixin, TaggedMixin):
    """Label metadata for a classification type without nested relations."""


class ClassificationShallow(BaseModelMixin, TaggedMixin):
    """Classification stub that links to choice and type names only."""

    choice_names: List[str] = Field(default_factory=list_of_str_factory)
    type_names: List[str] = Field(default_factory=list_of_str_factory)
