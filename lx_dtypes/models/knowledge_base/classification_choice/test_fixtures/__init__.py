import pytest

from lx_dtypes.models.knowledge_base.classification_choice_descriptor.ClassificationChoiceDescriptor import (
    ClassificationChoiceDescriptor,
)
from lx_dtypes.models.knowledge_base.classification_choice_descriptor.ClassificationChoiceDescriptorDjango import (
    ClassificationChoiceDescriptorDjango,
)

from ..ClassificationChoice import ClassificationChoice
from ..ClassificationChoiceDjango import (
    ClassificationChoiceDjango,
)


@pytest.fixture(scope="session")
def classification_choice_fixture(
    classification_choice_descriptor_fixture: ClassificationChoiceDescriptor,
) -> ClassificationChoice:
    """
    Create a sample ClassificationChoice instance for tests.

    The returned instance has name "sample_classification_choice", its
    classification_choice_descriptors set to a list containing the provided
    descriptor's name, and tags set to ["tag1", "tag2"].

    Parameters:
        classification_choice_descriptor_fixture (ClassificationChoiceDescriptor):
            Descriptor whose `name` will be used in the returned choice's
            `classification_choice_descriptors` list.

    Returns:
        ClassificationChoice: A populated ClassificationChoice suitable for use in tests.
    """
    return ClassificationChoice(
        name="sample_classification_choice",
        classification_choice_descriptors=[
            classification_choice_descriptor_fixture.name
        ],
        tags=["tag1", "tag2"],
    )


@pytest.fixture()
def django_classification_choice_fixture(
    classification_choice_fixture: ClassificationChoice,
    django_classification_choice_descriptor_fixture: ClassificationChoiceDescriptorDjango,
) -> "ClassificationChoiceDjango":
    """
    Create a Django ClassificationChoice instance by syncing from the provided ClassificationChoice fixture and return the refreshed database object.

    Parameters:
        classification_choice_fixture (ClassificationChoice): Source model whose `ddict` is used to create the Django record.
        django_classification_choice_descriptor_fixture (ClassificationChoiceDescriptorDjango): Fixture ensuring related descriptor rows exist in the database before syncing.

    Returns:
        ClassificationChoiceDjango: The Django model instance populated from the database after syncing.
    """
    classification_choice_django = ClassificationChoiceDjango.sync_from_ddict(
        classification_choice_fixture.ddict
    )
    classification_choice_django.refresh_from_db()

    return classification_choice_django
