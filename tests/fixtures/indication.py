from pytest import fixture

from lx_dtypes.models.core.indication import Indication, IndicationType
from lx_dtypes.models.core.intervention import Intervention


@fixture
def sample_indication_type() -> IndicationType:
    return IndicationType(
        uuid="123e4567-e89b-12d3-a456-426614174000",
        name="endoscopy",
        description="Indications related to endoscopy procedures.",
        tags=["endoscopy", "procedure"],
    )


@fixture
def sample_indication(
    sample_indication_type: IndicationType, sample_intervention: Intervention
) -> Indication:
    return Indication(
        uuid="123e4567-e89b-12d3-a456-426614174001",
        name="screening_colonoscopy",
        description="Indication for screening colonoscopy procedures.",
        tags=["endoscopy", "procedure", "screening"],
        types={sample_indication_type.name: sample_indication_type},
        expected_interventions={sample_intervention.name: sample_intervention},
    )
