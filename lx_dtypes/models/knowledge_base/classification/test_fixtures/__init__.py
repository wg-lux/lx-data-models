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
    """
    Provide a sample ClassificationType used in tests.

    Returns:
        ClassificationType: Instance with name "sample_classification_type", description
        "This is a sample classification type for testing purposes.", and tags ["tagX", "tagY"].
    """
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
    """
    Create a sample Classification referencing provided choice and type fixtures.

    Parameters:
        classification_choice_fixture (ClassificationChoice): fixture whose `name` will be included in the `classification_choices` list.
        classification_type_fixture (ClassificationType): fixture whose `name` will be included in the `classification_types` list.

    Returns:
        Classification: a Classification named "sample_classification" with lists populated from the provided fixtures' names.
    """
    return Classification(
        name="sample_classification",
        classification_choices=[classification_choice_fixture.name],
        classification_types=[classification_type_fixture.name],
    )


@pytest.fixture()
def django_classification_type_fixture(
    classification_type_fixture: ClassificationType,
) -> "ClassificationTypeDjango":
    """
    Create and persist a ClassificationTypeDjango using the provided ClassificationType's ddict.

    The fixture constructs a Django model from the domain object's ddict, refreshes it from the database to ensure all DB-populated fields are loaded, and returns the saved Django instance.

    Parameters:
        classification_type_fixture (ClassificationType): Domain object whose `ddict` will be used to build the Django model.

    Returns:
        ClassificationTypeDjango: The persisted Django model instance corresponding to the provided classification type.
    """
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
    """
    Create and return a ClassificationDjango instance populated from the given Classification fixture and refreshed from the database.

    Parameters:
        classification_fixture (Classification): Source classification whose `ddict` is used to create the Django model.
        django_classification_type_fixture (ClassificationTypeDjango): Ensures the related classification type exists in the database.
        django_classification_choice_fixture (ClassificationChoiceDjango): Ensures related classification choice records exist in the database.

    Returns:
        ClassificationDjango: The Django model instance created from `classification_fixture.ddict` and refreshed from the database.
    """
    classification_django = ClassificationDjango.sync_from_ddict(
        classification_fixture.ddict
    )
    classification_django.refresh_from_db()

    return classification_django
