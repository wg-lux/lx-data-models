from typing import List

from pydantic import Field

from lx_dtypes.utils.factories.field_defaults import list_of_str_factory
from lx_dtypes.utils.mixins.base_model import BaseModelMixin
from lx_dtypes.utils.mixins.tags import TaggedMixin


class InterventionTypeShallow(BaseModelMixin, TaggedMixin):
    pass


class InterventionShallow(BaseModelMixin):
    """Model representing a medical intervention."""

    expected_intervention_names: List[str] = Field(default_factory=list_of_str_factory)
    causes_finding_names: List[str] = Field(default_factory=list_of_str_factory)  # TODO implement in source yamls
    type_names: List[str] = Field(default_factory=list_of_str_factory)
