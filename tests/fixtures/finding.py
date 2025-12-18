from pytest import fixture

from lx_dtypes.models.core.classification import Classification
from lx_dtypes.models.core.finding import Finding, FindingType
from lx_dtypes.models.core.intervention import Intervention


@fixture
def sample_finding_type() -> FindingType:
    return FindingType(
        name="Sample Finding Type",
        description="A sample finding type for testing.",
    )


@fixture
def sample_finding(
    sample_finding_type: FindingType,
    sample_classification: Classification,
    sample_intervention: Intervention,
) -> Finding:
    return Finding(
        name="Sample Finding",
        description="A sample finding for testing.",
        types={sample_finding_type.name: sample_finding_type},
        classifications={sample_classification.name: sample_classification},
        interventions={sample_intervention.name: sample_intervention},
    )
