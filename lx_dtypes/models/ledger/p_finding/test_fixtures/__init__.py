import pytest

from lx_dtypes.models.knowledge_base.finding._FindingDjango import (
    FindingDjango,
)
from lx_dtypes.models.ledger.p_examination.Django import (
    PExaminationDjango,
)
from lx_dtypes.models.ledger.p_finding_classifications.Django import (
    PFindingClassificationsDjango,
)
from lx_dtypes.models.ledger.p_interventions.Django import (
    PFindingInterventionsDjango,
)

from ..Django import PFindingDjango
from ..Pydantic import PFinding


@pytest.fixture()
def p_finding_fixture(
    django_p_examination_fixture: PExaminationDjango,
    django_finding_fixture: "FindingDjango",
) -> PFinding:
    instance = PFinding(
        finding=django_finding_fixture.name,
        patient_examination=str(django_p_examination_fixture.pk),
    )
    return instance


@pytest.fixture()
def django_p_finding_fixture(
    p_finding_fixture: PFinding,
) -> PFindingDjango:
    instance = PFindingDjango.sync_from_ddict(p_finding_fixture.ddict)
    instance.refresh_from_db()
    return instance


@pytest.fixture()
def django_populated_p_finding_fixture(
    django_p_finding_fixture: PFindingDjango,
    django_populated_p_finding_classifications_fixture: "PFindingClassificationsDjango",
    django_populated_p_finding_interventions_fixture: "PFindingInterventionsDjango",
) -> PFindingDjango:
    django_p_finding_fixture.refresh_from_db()
    # assert that finding classifications is linked
    all_classifications = django_p_finding_fixture.patient_finding_classifications.all()

    if django_populated_p_finding_classifications_fixture not in all_classifications:
        raise ValueError(
            "The django_p_finding_classifications_fixture is not linked to the django_p_finding_fixture."
        )

    # assert that finding interventions is linked
    all_interventions = django_p_finding_fixture.patient_finding_interventions.all()
    if django_populated_p_finding_interventions_fixture not in all_interventions:
        raise ValueError(
            "The django_p_finding_interventions_fixture is not linked to the django_p_finding_fixture."
        )
    return django_p_finding_fixture
