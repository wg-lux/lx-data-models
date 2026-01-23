import pytest

from lx_dtypes.models.knowledge_base.classification._ClassificationDjango import (
    ClassificationDjango,
)
from lx_dtypes.models.knowledge_base.classification.Classification import Classification
from lx_dtypes.models.knowledge_base.intervention.Intervention import Intervention
from lx_dtypes.models.knowledge_base.intervention.InterventionDjango import (
    InterventionDjango,
)

from .._Finding import Finding
from .._FindingDjango import FindingDjango
from .._FindingType import FindingType
from .._FindingTypeDjango import FindingTypeDjango


@pytest.fixture(scope="session")
def finding_type_fixture() -> FindingType:
    """
    Create a sample FindingType for tests.

    Returns:
        A FindingType with name "sample_finding_type", description "This is a sample finding type for testing purposes.", and tags ["tagX", "tagY"].
    """
    return FindingType(
        name="sample_finding_type",
        description="This is a sample finding type for testing purposes.",
        tags=["tagX", "tagY"],
    )


@pytest.fixture(scope="session")
def finding_fixture(
    finding_type_fixture: FindingType,
    classification_fixture: Classification,
    intervention_fixture: Intervention,
) -> Finding:
    """
    Create a sample Finding instance for tests.

    The returned Finding has name "sample_finding", a test description, tags ["tag1", "tag2"], and its classifications, interventions, and finding_types lists populated with the .name values of the provided fixtures.

    Parameters:
        finding_type_fixture (FindingType): FindingType whose `name` is added to `finding_types`.
        classification_fixture (Classification): Classification whose `name` is added to `classifications`.
        intervention_fixture (Intervention): Intervention whose `name` is added to `interventions`.

    Returns:
        Finding: A preconfigured Finding instance for use in tests.
    """
    return Finding(
        name="sample_finding",
        description="This is a sample finding for testing purposes.",
        tags=["tag1", "tag2"],
        classifications=[
            classification_fixture.name,
        ],
        interventions=[
            intervention_fixture.name,
        ],
        finding_types=[finding_type_fixture.name],
    )


@pytest.fixture()
def django_finding_type_fixture(
    finding_type_fixture: FindingType,
) -> "FindingTypeDjango":
    """
    Create a FindingTypeDjango instance synchronized from the given FindingType domain object.

    Parameters:
        finding_type_fixture (FindingType): Domain FindingType whose data will be used to create or update the Django model.

    Returns:
        FindingTypeDjango: The Django model instance representing the provided FindingType.
    """
    finding_type_django = FindingTypeDjango.sync_from_ddict(finding_type_fixture.ddict)

    return finding_type_django


@pytest.fixture()
def django_finding_fixture(
    finding_fixture: Finding,
    django_classification_fixture: ClassificationDjango,
    django_intervention_fixture: InterventionDjango,
    django_finding_type_fixture: FindingTypeDjango,
) -> "FindingDjango":
    """
    Create a Django-synced Finding model instance for use in tests.

    Returns:
        FindingDjango: A FindingDjango instance created from the provided Finding's ddict and refreshed from the database.
    """
    finding_django = FindingDjango.sync_from_ddict(finding_fixture.ddict)
    finding_django.refresh_from_db()
    return finding_django
