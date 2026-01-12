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
    classification_choice_django = ClassificationChoiceDjango.sync_from_ddict(
        classification_choice_fixture.ddict
    )
    classification_choice_django.refresh_from_db()

    return classification_choice_django
