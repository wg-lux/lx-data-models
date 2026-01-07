import pytest

from lx_dtypes.models.knowledge_base.indication.Indication import (
    Indication,
)
from lx_dtypes.models.knowledge_base.indication.IndicationType import (
    IndicationType,
)


@pytest.fixture(scope="session")
def indication_type_fixture() -> IndicationType:
    return IndicationType(
        name="sample_indication_type",
        description="This is a sample indication type for testing purposes.",
        tags=["tagA", "tagB"],
    )


@pytest.fixture(scope="session")
def indication_fixture(indication_type_fixture: IndicationType) -> Indication:
    return Indication(
        name="sample_indication",
        indication_types=[indication_type_fixture.name],
        tags=["tag1", "tag2"],
    )
