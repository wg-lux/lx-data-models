from pytest import fixture

from lx_dtypes.names import (
    ClassificationChoiceDescriptorTypes,
    NumericDistributionChoices,
)

from ..ClassificationChoiceDescriptor import ClassificationChoiceDescriptor


@fixture(scope="session")
def classification_choice_descriptor_fixture() -> ClassificationChoiceDescriptor:
    pydantic_model = ClassificationChoiceDescriptor(
        name="Sample Descriptor",
        descriptor_type=ClassificationChoiceDescriptorTypes.NUMERIC,
        numeric_distribution=NumericDistributionChoices.NORMAL,
        numeric_distribution_params={"mean": 0.0, "stddev": 1.0},
        unit="centimeters",
    )
    return pydantic_model
