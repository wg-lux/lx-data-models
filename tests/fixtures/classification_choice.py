from pytest import fixture

from lx_dtypes.models.core.classification_choice import ClassificationChoice
from lx_dtypes.models.core.classification_choice_descriptor import (
    ClassificationChoiceDescriptor,
)


@fixture
def sample_classification_choice(
    sample_classification_choice_descriptor_numeric: ClassificationChoiceDescriptor,
) -> ClassificationChoice:
    """Fixture for a sample ClassificationChoice model."""
    classification_choice = ClassificationChoice(
        name="Sample Classification Choice",
        description="A sample classification choice for testing.",
        classification_choice_descriptors=[
            sample_classification_choice_descriptor_numeric
        ],
    )
    return classification_choice
