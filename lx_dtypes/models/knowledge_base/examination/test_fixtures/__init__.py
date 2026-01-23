import pytest

from lx_dtypes.models.knowledge_base.finding._Finding import Finding
from lx_dtypes.models.knowledge_base.finding._FindingDjango import (
    FindingDjango,
)
from lx_dtypes.models.knowledge_base.indication.Indication import Indication
from lx_dtypes.models.knowledge_base.indication.IndicationDjango import (
    IndicationDjango,
)

from ..Examination import Examination
from ..ExaminationDjango import ExaminationDjango
from ..ExaminationType import ExaminationType
from ..ExaminationTypeDjango import (
    ExaminationTypeDjango,
)


@pytest.fixture(scope="session")
def examination_type_fixture() -> ExaminationType:
    """
    Create a sample ExaminationType used by tests.

    Returns:
        ExaminationType: An instance with name "sample_examination_type", description "This is a sample examination type for testing purposes.", and tags ["tagA", "tagB"].
    """
    return ExaminationType(
        name="sample_examination_type",
        description="This is a sample examination type for testing purposes.",
        tags=["tagA", "tagB"],
    )


@pytest.fixture(scope="session")
def examination_fixture(
    examination_type_fixture: ExaminationType,
    finding_fixture: Finding,
    indication_fixture: Indication,
) -> Examination:
    """
    Create a sample Examination instance that references the provided fixtures by name.

    Parameters:
        examination_type_fixture (ExaminationType): Fixture whose `name` will be placed into the examination's `examination_types`.
        finding_fixture (Finding): Fixture whose `name` will be placed into the examination's `findings`.
        indication_fixture (Indication): Fixture whose `name` will be placed into the examination's `indications`.

    Returns:
        examination (Examination): An Examination populated with sample name, description, tags, and associations to the provided fixtures' names.
    """
    return Examination(
        name="sample_examination",
        description="This is a sample examination for testing purposes.",
        tags=["tag1", "tag2"],
        examination_types=[examination_type_fixture.name],
        findings=[finding_fixture.name],
        indications=[indication_fixture.name],
    )


@pytest.fixture()
def django_examination_type_fixture(
    examination_type_fixture: ExaminationType,
) -> "ExaminationTypeDjango":
    """
    Create and return a Django ExaminationType model synchronized from the provided domain fixture.

    Parameters:
        examination_type_fixture (ExaminationType): Domain model fixture whose ddict representation will be used to create or update the ExaminationTypeDjango.

    Returns:
        ExaminationTypeDjango: The synchronized Django ExaminationType instance.
    """
    examination_type_django = ExaminationTypeDjango.sync_from_ddict(
        examination_type_fixture.ddict
    )

    return examination_type_django


@pytest.fixture()
def django_examination_fixture(
    examination_fixture: Examination,
    django_examination_type_fixture: ExaminationTypeDjango,
    django_finding_fixture: FindingDjango,
    django_indication_fixture: IndicationDjango,
) -> "ExaminationDjango":
    """
    Create an ExaminationDjango instance synchronized from the supplied examination fixture.

    Parameters:
        examination_fixture (Examination): Domain object whose ddict is used to create the Django instance.
        django_examination_type_fixture (ExaminationTypeDjango): Ensures the related ExaminationType Django record exists.
        django_finding_fixture (FindingDjango): Ensures related Finding Django records exist.
        django_indication_fixture (IndicationDjango): Ensures related Indication Django records exist.

    Returns:
        ExaminationDjango: The ExaminationDjango instance created from the fixture and refreshed from the database.
    """
    examination_django = ExaminationDjango.sync_from_ddict(examination_fixture.ddict)
    examination_django.refresh_from_db()
    return examination_django
