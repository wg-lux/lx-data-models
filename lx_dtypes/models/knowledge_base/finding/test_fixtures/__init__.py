import pytest

from lx_dtypes.models.knowledge_base.classification.Classification import Classification
from lx_dtypes.models.knowledge_base.intervention.Intervention import Intervention

from ..Finding import Finding
from ..FindingType import FindingType


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
