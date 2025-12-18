from pytest import fixture

from lx_dtypes.models.core.classification import Classification, ClassificationType
from lx_dtypes.models.core.classification_choice import ClassificationChoice


@fixture
def sample_classification_type() -> ClassificationType:
    return ClassificationType(
        name="Sample Classification Type",
        description="A sample classification type for testing.",
    )


@fixture
def sample_classification(
    sample_classification_type: ClassificationType,
    sample_classification_choice: ClassificationChoice,
) -> Classification:
    classification_choice_name = sample_classification_choice.name
    classification_type_name = sample_classification_type.name
    return Classification(
        name="Sample Classification",
        description="A sample classification for testing.",
        types={classification_type_name: sample_classification_type},
        classification_choices={
            classification_choice_name: sample_classification_choice
        },
    )
