import pytest

from lx_dtypes.models.knowledge_base.intervention.InterventionDjango import (
    InterventionDjango,
)
from lx_dtypes.models.knowledge_base.intervention.InterventionTypeDjango import (
    InterventionTypeDjango,
)

from ..Intervention import Intervention
from ..InterventionType import InterventionType


@pytest.fixture(scope="session")
def intervention_type_fixture() -> InterventionType:
    """
    Create a sample InterventionType used in tests.

    Returns:
        InterventionType: an InterventionType instance with name "sample_intervention_type", description "This is a sample intervention type for testing purposes.", and tags ["tagA", "tagB"].
    """
    return InterventionType(
        name="sample_intervention_type",
        description="This is a sample intervention type for testing purposes.",
        tags=["tagA", "tagB"],
    )


@pytest.fixture(scope="session")
def intervention_fixture(intervention_type_fixture: InterventionType) -> Intervention:
    """
    Constructs a sample Intervention for tests that references the given InterventionType by name.

    Parameters:
        intervention_type_fixture (InterventionType): The InterventionType whose name will be included in the returned Intervention's `intervention_types` list.

    Returns:
        Intervention: An Intervention populated with name "sample_intervention", a brief description, tags ["tag1", "tag2"], and `intervention_types` set to a list containing `intervention_type_fixture.name`.
    """
    return Intervention(
        name="sample_intervention",
        description="This is a sample intervention for testing purposes.",
        tags=["tag1", "tag2"],
        intervention_types=[intervention_type_fixture.name],
    )


@pytest.fixture()
def django_intervention_type_fixture(
    intervention_type_fixture: InterventionType,
) -> "InterventionTypeDjango":
    """
    Create a Django InterventionType model from the provided test InterventionType.

    Parameters:
        intervention_type_fixture (InterventionType): Sample InterventionType used in tests; its ddict representation is used to create the Django model.

    Returns:
        InterventionTypeDjango: Django model instance synchronized from the fixture's ddict.
    """
    intervention_type_django = InterventionTypeDjango.sync_from_ddict(
        intervention_type_fixture.ddict
    )

    return intervention_type_django


@pytest.fixture()
def django_intervention_fixture(
    intervention_fixture: Intervention,
    django_intervention_type_fixture: InterventionTypeDjango,
) -> "InterventionDjango":
    """
    Create a Django Intervention model instance from a test Intervention object.

    Parameters:
        intervention_fixture (Intervention): The test Intervention whose data will be synced into the Django model.
        django_intervention_type_fixture (InterventionTypeDjango): The Django InterventionType corresponding to the intervention's type; supplied to ensure the related type exists before syncing.

    Returns:
        InterventionDjango: The Django Intervention instance created or updated from the provided Intervention's ddict.
    """
    intervention_django = InterventionDjango.sync_from_ddict(intervention_fixture.ddict)

    return intervention_django
