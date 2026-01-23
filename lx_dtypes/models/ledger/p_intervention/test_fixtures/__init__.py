import pytest

from lx_dtypes.models.knowledge_base.intervention.InterventionDjango import (
    InterventionDjango,
)
from lx_dtypes.models.ledger.p_interventions.Django import (
    PFindingInterventionsDjango,
)

from ..Django import PFindingInterventionDjango
from ..Pydantic import PFindingIntervention


@pytest.fixture()
def p_finding_intervention_fixture(
    django_p_finding_interventions_fixture: "PFindingInterventionsDjango",
    django_intervention_fixture: InterventionDjango,
) -> PFindingIntervention:
    instance = PFindingIntervention(
        intervention=str(django_intervention_fixture.pk),
        patient_finding_interventions=str(django_p_finding_interventions_fixture.pk),
    )
    return instance


@pytest.fixture()
def django_p_finding_intervention_fixture(
    p_finding_intervention_fixture: PFindingIntervention,
) -> PFindingInterventionDjango:
    instance = PFindingInterventionDjango.sync_from_ddict(
        p_finding_intervention_fixture.ddict
    )
    instance.refresh_from_db()
    return instance
