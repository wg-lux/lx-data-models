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
    """
    Provide a reusable sample IndicationType instance for tests.

    The returned instance has:
    - name: "sample_indication_type"
    - description: "This is a sample indication type for testing purposes."
    - tags: ["tagA", "tagB"]

    Returns:
        IndicationType: A preconfigured IndicationType object suitable for use in test fixtures.
    """
    return IndicationType(
        name="sample_indication_type",
        description="This is a sample indication type for testing purposes.",
        tags=["tagA", "tagB"],
    )


@pytest.fixture(scope="session")
def indication_fixture(indication_type_fixture: IndicationType) -> Indication:
    """
    Create a test Indication domain object linked to the provided IndicationType.

    Parameters:
        indication_type_fixture (IndicationType): The IndicationType whose `name` will be included in the returned Indication's `indication_types` list.

    Returns:
        Indication: An Indication with name "sample_indication", `indication_types` set to [indication_type_fixture.name], and tags ["tag1", "tag2"].
    """
    return Indication(
        name="sample_indication",
        indication_types=[indication_type_fixture.name],
        tags=["tag1", "tag2"],
    )


@pytest.fixture()
def django_indication_type_fixture(
    indication_type_fixture: IndicationType,
) -> "IndicationTypeDjango":
    """
    Create an IndicationTypeDjango instance from a domain IndicationType for tests.

    Parameters:
        indication_type_fixture (IndicationType): Domain IndicationType to convert.

    Returns:
        IndicationTypeDjango: Django-adapted IndicationType synchronized from the provided domain object.
    """
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
    """
    Create and return an IndicationDjango populated from the provided domain Indication's ddict.

    Parameters:
        indication_fixture (Indication): Domain Indication whose ddict is used to populate the Django model.
        django_intervention_fixture (InterventionDjango): Fixture providing an InterventionDjango required by tests (not directly used here).
        django_indication_type_fixture (IndicationTypeDjango): Fixture providing an IndicationTypeDjango required by tests (not directly used here).

    Returns:
        IndicationDjango: A Django-model instance synchronized from the domain indication's ddict.
    """
    indication_django = IndicationDjango.sync_from_ddict(indication_fixture.ddict)

    return indication_django
