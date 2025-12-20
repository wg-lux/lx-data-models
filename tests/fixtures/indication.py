from pytest import fixture

from lx_dtypes.contrib.lx_django.models.core.indication import (
    Indication as DjangoIndicationModel,
)
from lx_dtypes.contrib.lx_django.models.core.indication import (
    IndicationType as DjangoIndicationTypeModel,
)
from lx_dtypes.contrib.lx_django.models.core.intervention import (
    Intervention as DjangoInterventionModel,
)
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


@fixture(scope="function")
def sample_django_indication_type(
    sample_indication_type: IndicationType,
) -> DjangoIndicationTypeModel:
    ddict = sample_indication_type.to_ddict_shallow()
    django_indication_type = DjangoIndicationTypeModel.sync_from_ddict_shallow(ddict)

    django_indication_type.refresh_from_db()
    return django_indication_type


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


@fixture(scope="function")
def sample_django_indication(
    sample_indication: Indication,
    sample_django_indication_type: DjangoIndicationTypeModel,
    sample_django_intervention: DjangoInterventionModel,
) -> DjangoIndicationModel:
    ddict = sample_indication.to_ddict_shallow()
    django_indication = DjangoIndicationModel.sync_from_ddict_shallow(ddict)

    django_indication.refresh_from_db()
    return django_indication
