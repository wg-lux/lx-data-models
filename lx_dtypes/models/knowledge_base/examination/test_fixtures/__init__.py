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
    examination_django = ExaminationDjango.sync_from_ddict(examination_fixture.ddict)
    examination_django.refresh_from_db()
    return examination_django
