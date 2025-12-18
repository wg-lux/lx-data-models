from pytest import fixture

from lx_dtypes.models.core.intervention import Intervention, InterventionType


@fixture
def sample_intervention_type() -> InterventionType:
    return InterventionType(
        name="Sample Intervention Type",
        description="A sample intervention type for testing purposes.",
    )


@fixture
def sample_intervention(sample_intervention_type: InterventionType) -> Intervention:
    return Intervention(
        name="Sample Intervention",
        description="A sample intervention for testing purposes.",
        types=[sample_intervention_type],
    )
