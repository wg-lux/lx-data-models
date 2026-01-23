from typing import Dict, Union

# NUMERIC_DISTRIBUTION_PARAMS_DICT_TYPE = Dict[
#     str, Union[str, float, int]
# ]  # TODO Improve typing when we know which descriptors are expected by the implemented distributions


# class NumericDistributionParamsDict(NUMERIC_DISTRIBUTION_PARAMS_DICT_TYPE):
#     pass


def numeric_distribution_params_dict_factory() -> Dict[str, Union[str, float, int]]:
    """
    Create a new empty dictionary for numeric distribution parameters keyed by name.

    Returns:
        Dict[str, Union[str, float, int]]: A fresh empty mapping from parameter names to string, float, or int values.
    """
    return dict()


def selection_default_options_dict_factory() -> Dict[str, float]:
    """
    Create a new empty dictionary intended to map selection option names to their default float values.

    Returns:
        Dict[str, float]: A fresh empty dictionary where keys are option names and values are default floats.
    """
    return dict()
