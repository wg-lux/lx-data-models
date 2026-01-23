from typing import Dict, Union

from lx_dtypes.models.base.app_base_model.ddict import KnowledgebaseBaseModelDataDict
from lx_dtypes.names import (
    ClassificationChoiceDescriptorTypes,
    NumericDistributionChoices,
)


class ClassificationChoiceDescriptorDataDict(KnowledgebaseBaseModelDataDict):
    classification_choice_descriptor_type: ClassificationChoiceDescriptorTypes
    unit: str
    numeric_min: float
    numeric_max: float
    numeric_distribution: NumericDistributionChoices
    numeric_distribution_params: Dict[str, Union[str, float, int]]
    text_max_length: int
    default_value_str: str
    default_value_num: float
    default_value_bool: bool
    selection_options: list[str]
    selection_multiple: bool
    selection_multiple_n_min: int
    selection_multiple_n_max: int
    selection_default_options: Dict[str, float]
