from pytest import fixture

from lx_dtypes.contrib.lx_django.models.core.intervention import (
    Intervention as DjangoInterventionModel,
)
from lx_dtypes.contrib.lx_django.models.core.intervention import (
    InterventionType as DjangoInterventionTypeModel,
)
from lx_dtypes.models.core.intervention import Intervention, InterventionType


@fixture
def sample_intervention_type() -> InterventionType:
    return InterventionType(
        name="Sample Intervention Type",
        description="A sample intervention type for testing purposes.",
    )


@fixture(scope="function")
def sample_django_intervention_type(
    sample_intervention_type: InterventionType,
) -> DjangoInterventionTypeModel:
    ddict = sample_intervention_type.to_ddict_shallow()
    django_intervention_type = DjangoInterventionTypeModel.sync_from_ddict_shallow(
        ddict
    )

    django_intervention_type.refresh_from_db()
    return django_intervention_type


@fixture
def sample_intervention(sample_intervention_type: InterventionType) -> Intervention:
    return Intervention(
        name="Sample Intervention",
        description="A sample intervention for testing purposes.",
        types={sample_intervention_type.name: sample_intervention_type},
    )


@fixture(scope="function")
def sample_django_intervention(
    sample_intervention: Intervention,
    sample_django_intervention_type: DjangoInterventionTypeModel,
) -> DjangoInterventionModel:
    ddict = sample_intervention.to_ddict_shallow()
    django_intervention = DjangoInterventionModel.sync_from_ddict_shallow(ddict)

    django_intervention.refresh_from_db()
    return django_intervention
