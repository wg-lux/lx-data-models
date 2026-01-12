import pytest

from lx_dtypes.models.knowledge_base.classification.Classification import Classification
from lx_dtypes.models.knowledge_base.classification.ClassificationDjango import (
    ClassificationDjango,
)
from lx_dtypes.models.knowledge_base.intervention.Intervention import Intervention
from lx_dtypes.models.knowledge_base.intervention.InterventionDjango import (
    InterventionDjango,
)

from ..Finding import Finding
from ..FindingDjango import FindingDjango
from ..FindingType import FindingType
from ..FindingTypeDjango import FindingTypeDjango


@pytest.fixture(scope="session")
def finding_type_fixture() -> FindingType:
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
    finding_type_django = FindingTypeDjango.sync_from_ddict(finding_type_fixture.ddict)

    return finding_type_django


@pytest.fixture()
def django_finding_fixture(
    finding_fixture: Finding,
    django_classification_fixture: ClassificationDjango,
    django_intervention_fixture: InterventionDjango,
    django_finding_type_fixture: FindingTypeDjango,
) -> "FindingDjango":
    finding_django = FindingDjango.sync_from_ddict(finding_fixture.ddict)

    return finding_django
