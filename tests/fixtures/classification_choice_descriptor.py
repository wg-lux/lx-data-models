from pytest import fixture

from lx_dtypes.models.core.classification_choice_descriptor import (
    ClassificationChoiceDescriptor,
)


@fixture(scope="session")
def sample_classification_choice_descriptor_numeric() -> ClassificationChoiceDescriptor:
    classification_choice_descriptor = ClassificationChoiceDescriptor(
        descriptor_type="numeric", name="Sample Numeric Descriptor", tags=[], unit=None
    )

    return classification_choice_descriptor
