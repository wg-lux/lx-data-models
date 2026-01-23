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
    """
    Create a PFinding Pydantic instance initialized from the provided Django fixtures.

    Parameters:
        django_p_examination_fixture (PExaminationDjango): Django patient examination instance whose primary key is used as the PFinding.patient_examination (converted to string).
        django_finding_fixture (FindingDjango): Django finding instance whose name is used as the PFinding.finding.

    Returns:
        PFinding: A PFinding instance with `finding` set to the finding name and `patient_examination` set to the examination primary key as a string.
    """
    instance = PFinding(
        finding=django_finding_fixture.name,
        patient_examination=str(django_p_examination_fixture.pk),
    )
    return instance


@pytest.fixture()
def django_p_finding_fixture(
    p_finding_fixture: PFinding,
) -> PFindingDjango:
    """
    Create a PFindingDjango ORM instance from a PFinding pydantic fixture and refresh it from the database.

    Parameters:
        p_finding_fixture (PFinding): Pydantic PFinding instance whose `ddict` is used to construct the ORM object.

    Returns:
        PFindingDjango: A PFindingDjango instance refreshed from the database.
    """
    instance = PFindingDjango.sync_from_ddict(p_finding_fixture.ddict)
    instance.refresh_from_db()
    return instance


@pytest.fixture()
def django_populated_p_finding_fixture(
    django_p_finding_fixture: PFindingDjango,
    django_populated_p_finding_classifications_fixture: "PFindingClassificationsDjango",
    django_populated_p_finding_interventions_fixture: "PFindingInterventionsDjango",
) -> PFindingDjango:
    """
    Verify that the given PFindingDjango instance is refreshed from the database and has the provided classifications and interventions linked, then return the refreshed instance.

    Parameters:
        django_p_finding_fixture (PFindingDjango): The PFindingDjango instance to refresh and verify.
        django_populated_p_finding_classifications_fixture (PFindingClassificationsDjango): The expected classifications ORM instance that must be related to the finding.
        django_populated_p_finding_interventions_fixture (PFindingInterventionsDjango): The expected interventions ORM instance that must be related to the finding.

    Returns:
        PFindingDjango: The refreshed PFindingDjango instance.

    Raises:
        ValueError: If the provided classifications or interventions fixture is not linked to the finding.
    """
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
