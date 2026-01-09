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
    return InterventionType(
        name="sample_intervention_type",
        description="This is a sample intervention type for testing purposes.",
        tags=["tagA", "tagB"],
    )


@pytest.fixture(scope="session")
def intervention_fixture(intervention_type_fixture: InterventionType) -> Intervention:
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
    intervention_type_django = InterventionTypeDjango.sync_from_ddict(
        intervention_type_fixture.ddict
    )

    return intervention_type_django


@pytest.fixture()
def django_intervention_fixture(
    intervention_fixture: Intervention,
) -> "InterventionDjango":
    intervention_django = InterventionDjango.sync_from_ddict(intervention_fixture.ddict)

    return intervention_django
