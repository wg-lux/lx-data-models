from typing import Dict, Union

from pydantic import Field

from lx_dtypes.factories.typed_dicts import (
    # NumericDistributionParamsDict,
    numeric_distribution_params_dict_factory,
)
from lx_dtypes.models.knowledge_base.classification_choice_descriptor.DescriptorTypeMixin import (
    DescriptorTypeMixin,
)
from lx_dtypes.names import NumericDistributionChoices


class NumericDescriptorMixin(DescriptorTypeMixin):
    numeric_min: float = Field(default_factory=lambda: float("-inf"))
    numeric_max: float = Field(default_factory=lambda: float("inf"))
    numeric_distribution: NumericDistributionChoices = Field(
        default_factory=lambda: NumericDistributionChoices.UNKNOWN
    )
    numeric_distribution_params: Dict[str, Union[str, float, int]] = Field(
        default_factory=numeric_distribution_params_dict_factory
    )
    default_value_num: float = Field(default_factory=lambda: float(-999))
