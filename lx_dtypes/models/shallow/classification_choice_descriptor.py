from typing import Dict, Literal, Optional, Union

from pydantic import Field

from lx_dtypes.utils.factories.field_defaults import str_unknown_factory
from lx_dtypes.utils.mixins.base_model import AppBaseModel


class ClassificationChoiceDescriptorShallow(AppBaseModel):
    name: str
    description: str = Field(default_factory=str_unknown_factory)
    descriptor_type: Literal["numeric", "text", "boolean", "selection"] = Field(
        default_factory=lambda: "text"
    )
    unit_name: Optional[str] = None
    numeric_min: float = Field(default_factory=lambda: float("-inf"))
    numeric_max: float = Field(default_factory=lambda: float("inf"))
    numeric_distribution: Literal["normal", "uniform", "exponential", "unknown"] = (
        Field(default_factory=lambda: "normal")
    )
    numeric_distribution_params: Dict[str, Union[str, float, int]] = Field(
        default_factory=dict
    )  # TODO Improve typing when we know which descriptors are expected by the implemented distributions
    text_max_length: int = Field(default_factory=lambda: 255)
    default_value_str: str = Field(default_factory=str_unknown_factory)
    default_value_num: float = Field(default_factory=lambda: float("nan"))
    default_value_bool: bool = False
    selection_options: list[str] = Field(default_factory=list)
    selection_multiple: bool = False
    selection_multiple_n_min: int = Field(default_factory=lambda: 0)
    selection_multiple_n_max: int = Field(default_factory=lambda: 1)
    selection_default_options: Dict[str, float] = Field(
        default_factory=dict
    )  # option name -> probability
