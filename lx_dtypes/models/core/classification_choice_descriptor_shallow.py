from typing import Dict, Literal, Optional, Union

from pydantic import Field

from lx_dtypes.models.base_models.base_model import (
    AppBaseModelNamesUUIDTags,
    AppBaseModelNamesUUIDTagsDataDict,
)
from lx_dtypes.utils.factories.field_defaults import str_unknown_factory


class ClassificationChoiceDescriptorShallowDataDict(AppBaseModelNamesUUIDTagsDataDict):
    descriptor_type: Literal["numeric", "text", "boolean", "selection"]
    unit_name: Optional[str]
    numeric_min: float
    numeric_max: float
    numeric_distribution: Literal["normal", "uniform", "exponential", "unknown"]
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


class ClassificationChoiceDescriptorShallow(AppBaseModelNamesUUIDTags):
    """
    Describes how a classification choice captures user input (type, defaults, bounds).
    Inherits from BaseModelMixin for common model functionality.

    Attributes:
        name (str): The name of the descriptor.
        description (str): A textual description of the descriptor.
        descriptor_type (Literal): The type of data the descriptor captures.
        unit_name (Optional[str]): The name of the unit associated with the descriptor, if applicable.
        numeric_min (float): The minimum value for numeric descriptors.
        numeric_max (float): The maximum value for numeric descriptors.
        numeric_distribution (Literal): The assumed distribution of numeric values.
        numeric_distribution_params (Dict[str, Union[str, float, int]]): Parameters for the numeric distribution.
        text_max_length (int): The maximum length for text descriptors.
        default_value_str (str): The default string value for text descriptors.
        default_value_num (float): The default numeric value for numeric descriptors.
        default_value_bool (bool): The default boolean value for boolean descriptors.
        selection_options (list[str]): The list of options for selection descriptors.
        selection_multiple (bool): Indicates if multiple selections are allowed.
        selection_multiple_n_min (int): Minimum number of selections allowed.
        selection_multiple_n_max (int): Maximum number of selections allowed.
        selection_default_options (Dict[str, float]): Default options with their probabilities for selection descriptors.
    """

    name: str
    # description: str = Field(default_factory=str_unknown_factory)
    descriptor_type: Literal["numeric", "text", "boolean", "selection"] = Field(
        default_factory=lambda: "text"
    )
    unit_name: Optional[str] = None
    numeric_min: float = Field(default_factory=lambda: float("-inf"))
    numeric_max: float = Field(default_factory=lambda: float("inf"))
    numeric_distribution: Literal["normal", "uniform", "exponential", "unknown"] = (
        Field(default_factory=lambda: "unknown")
    )
    numeric_distribution_params: Dict[str, Union[str, float, int]] = Field(
        default_factory=dict
    )  # TODO Improve typing when we know which descriptors are expected by the implemented distributions
    text_max_length: int = Field(default_factory=lambda: 255)
    default_value_str: str = Field(default_factory=str_unknown_factory)
    default_value_num: float = Field(default_factory=lambda: float(-999))
    default_value_bool: bool = False
    selection_options: list[str] = Field(default_factory=list)
    selection_multiple: bool = False
    selection_multiple_n_min: int = Field(default_factory=lambda: 0)
    selection_multiple_n_max: int = Field(default_factory=lambda: 1)
    selection_default_options: Dict[str, float] = Field(
        default_factory=dict
    )  # option name -> probability

    @property
    def ddict_shallow(self) -> type[ClassificationChoiceDescriptorShallowDataDict]:
        return ClassificationChoiceDescriptorShallowDataDict

    def to_ddict_shallow(self) -> ClassificationChoiceDescriptorShallowDataDict:
        data_dict = self.ddict_shallow(**self.model_dump())
        return data_dict
