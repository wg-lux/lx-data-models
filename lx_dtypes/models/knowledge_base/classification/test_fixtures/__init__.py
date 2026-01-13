import pytest

from lx_dtypes.models.knowledge_base.classification_choice.ClassificationChoice import (
    ClassificationChoice,
)
from lx_dtypes.models.knowledge_base.classification_choice.ClassificationChoiceDjango import (
    ClassificationChoiceDjango,
)

from ..Classification import Classification
from .._ClassificationDjango import ClassificationDjango
from ..ClassificationType import ClassificationType
from .._ClassificationTypeDjango import ClassificationTypeDjango


@pytest.fixture(scope="session")
def classification_type_fixture() -> ClassificationType:
    return ClassificationType(
        name="sample_classification_type",
        description="This is a sample classification type for testing purposes.",
        tags=["tagX", "tagY"],
    )


@pytest.fixture(scope="session")
def classification_fixture(
    classification_choice_fixture: ClassificationChoice,
    classification_type_fixture: ClassificationType,
) -> Classification:
    return Classification(
        name="sample_classification",
        classification_choices=[classification_choice_fixture.name],
        classification_types=[classification_type_fixture.name],
    )


@pytest.fixture()
def django_classification_type_fixture(
    classification_type_fixture: ClassificationType,
) -> "ClassificationTypeDjango":
    classification_type_django = ClassificationTypeDjango.sync_from_ddict(
        classification_type_fixture.ddict
    )
    classification_type_django.refresh_from_db()

    return classification_type_django


@pytest.fixture()
def django_classification_fixture(
    classification_fixture: Classification,
    django_classification_type_fixture: ClassificationTypeDjango,
    django_classification_choice_fixture: "ClassificationChoiceDjango",
) -> "ClassificationDjango":
    classification_django = ClassificationDjango.sync_from_ddict(
        classification_fixture.ddict
    )
    classification_django.refresh_from_db()

    return classification_django
