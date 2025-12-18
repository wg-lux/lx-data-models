from pytest import fixture

from lx_dtypes.models.core.finding import Finding, FindingType


@fixture
def sample_finding_type() -> FindingType:
    return FindingType(
        name="Sample Finding Type",
        description="A sample finding type for testing.",
    )


@fixture
def sample_finding(
    sample_finding_type: FindingType,
) -> Finding:
    finding_type_name = sample_finding_type.name
    return Finding(
        name="Sample Finding",
        description="A sample finding for testing.",
        type_names=[finding_type_name],
    )
