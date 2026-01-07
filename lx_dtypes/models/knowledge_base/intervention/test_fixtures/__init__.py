import pytest

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
