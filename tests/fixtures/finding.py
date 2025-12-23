from lx_dtypes.lx_django.models.core.classification import (
    Classification as DjangoClassificationModel,
)
from lx_dtypes.lx_django.models.core.finding import (
    Finding as DjangoFindingModel,
)
from lx_dtypes.lx_django.models.core.finding import (
    FindingType as DjangoFindingTypeModel,
)
from lx_dtypes.lx_django.models.core.intervention import (
    Intervention as DjangoInterventionModel,
)
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


@fixture(scope="function")
def sample_django_finding_type(
    sample_finding_type: FindingType,
) -> DjangoFindingTypeModel:
    ddict = sample_finding_type.to_ddict_shallow()
    django_finding_type = DjangoFindingTypeModel.sync_from_ddict_shallow(ddict)

    django_finding_type.refresh_from_db()
    return django_finding_type


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


@fixture(scope="function")
def sample_django_finding(
    sample_finding: Finding,
    sample_django_finding_type: DjangoFindingTypeModel,
    sample_django_classification: DjangoClassificationModel,
    sample_django_intervention: DjangoInterventionModel,
) -> DjangoFindingModel:
    ddict = sample_finding.to_ddict_shallow()
    django_finding = DjangoFindingModel.sync_from_ddict_shallow(ddict)

    django_finding.refresh_from_db()
    return django_finding
