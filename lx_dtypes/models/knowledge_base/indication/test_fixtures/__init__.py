import pytest

from lx_dtypes.models.knowledge_base.indication.Indication import (
    Indication,
)
from lx_dtypes.models.knowledge_base.indication.IndicationType import (
    IndicationType,
)
from lx_dtypes.models.knowledge_base.intervention.InterventionDjango import (
    InterventionDjango,
)

from ..IndicationDjango import IndicationDjango
from ..IndicationTypeDjango import IndicationTypeDjango


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


@pytest.fixture()
def django_indication_type_fixture(
    indication_type_fixture: IndicationType,
) -> "IndicationTypeDjango":
    indication_type_django = IndicationTypeDjango.sync_from_ddict(
        indication_type_fixture.ddict
    )

    return indication_type_django


@pytest.fixture()
def django_indication_fixture(
    indication_fixture: Indication,
    django_intervention_fixture: InterventionDjango,
    django_indication_type_fixture: IndicationTypeDjango,
) -> "IndicationDjango":
    indication_django = IndicationDjango.sync_from_ddict(indication_fixture.ddict)

    return indication_django
