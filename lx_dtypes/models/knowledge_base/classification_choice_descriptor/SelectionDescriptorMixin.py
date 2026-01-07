from typing import Dict

from pydantic import Field

from lx_dtypes.models.knowledge_base.classification_choice_descriptor.DescriptorTypeMixin import (
    DescriptorTypeMixin,
)


class SelectionDescriptorMixin(DescriptorTypeMixin):
    selection_options: list[str] = Field(default_factory=list)
    selection_multiple: bool = False
    selection_multiple_n_min: int = Field(default_factory=lambda: 0)
    selection_multiple_n_max: int = Field(default_factory=lambda: 1)
    selection_default_options: Dict[str, float] = Field(
        default_factory=dict
    )  # option name -> probability
