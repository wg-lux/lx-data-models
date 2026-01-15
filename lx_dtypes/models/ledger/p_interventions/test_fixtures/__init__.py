import pytest

from lx_dtypes.models.knowledge_base.intervention.InterventionDjango import (
    InterventionDjango,
)
from lx_dtypes.models.ledger.p_finding.Django import (
    PFindingDjango,
)
from lx_dtypes.models.ledger.p_intervention.Django import (
    PFindingInterventionDjango,
)

from ..Django import PFindingInterventionsDjango
from ..Pydantic import PFindingInterventions


@pytest.fixture()
def p_finding_interventions_fixture(
    django_intervention_fixture: InterventionDjango,
    django_p_finding_fixture: PFindingDjango,
) -> PFindingInterventions:
    instance = PFindingInterventions(
        patient_finding=str(django_p_finding_fixture.pk),
        # patient_finding_interventions=[],
    )
    return instance


@pytest.fixture()
def django_p_finding_interventions_fixture(
    p_finding_interventions_fixture: PFindingInterventions,
) -> PFindingInterventionsDjango:
    instance = PFindingInterventionsDjango.sync_from_ddict(
        p_finding_interventions_fixture.ddict
    )
    instance.refresh_from_db()
    return instance


@pytest.fixture()
def django_populated_p_finding_interventions_fixture(
    django_p_finding_intervention_fixture: PFindingInterventionDjango,
    django_p_finding_interventions_fixture: PFindingInterventionsDjango,
) -> PFindingInterventionsDjango:
    django_p_finding_interventions_fixture.refresh_from_db()
    # assert that finding interventions is linked
    all_interventions = (
        django_p_finding_interventions_fixture.patient_finding_interventions.all()
    )
    if django_p_finding_intervention_fixture not in all_interventions:
        raise ValueError(
            "The django_p_finding_intervention_fixture is not linked to the p_finding_interventions_fixture."
        )
    return django_p_finding_interventions_fixture
