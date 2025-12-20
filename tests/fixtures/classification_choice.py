from pytest import fixture

from lx_dtypes.contrib.lx_django.models.core.classification_choice import (
    ClassificationChoice as DjangoClassificationChoiceModel,
)
from lx_dtypes.contrib.lx_django.models.core.classification_choice_descriptor import (
    ClassificationChoiceDescriptor as DjangoClassificationChoiceDescriptorModel,
)
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


@fixture(scope="function")
def sample_django_classification_choice(
    sample_classification_choice: ClassificationChoice,
    sample_django_classification_choice_descriptor_numeric: DjangoClassificationChoiceDescriptorModel,
):
    """Fixture for a sample DjangoClassificationChoice model."""
    ddict = sample_classification_choice.to_ddict_shallow()
    django_classification_choice = (
        DjangoClassificationChoiceModel.sync_from_ddict_shallow(ddict)
    )

    django_classification_choice.refresh_from_db()
    return django_classification_choice
