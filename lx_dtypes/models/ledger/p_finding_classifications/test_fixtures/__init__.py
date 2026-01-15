import pytest

from lx_dtypes.models.ledger.p_finding.Django import PFindingDjango
from lx_dtypes.models.ledger.p_finding_classification_choice.Django import (
    PFindingClassificationChoiceDjango,
)

from ..Django import PFindingClassificationsDjango
from ..Pydantic import PFindingClassifications


@pytest.fixture()
def p_finding_classifications_fixture(
    django_p_finding_fixture: PFindingDjango,
) -> PFindingClassifications:
    instance = PFindingClassifications(
        patient_finding=str(django_p_finding_fixture.pk),
    )
    return instance


@pytest.fixture()
def django_p_finding_classifications_fixture(
    p_finding_classifications_fixture: PFindingClassifications,
) -> PFindingClassificationsDjango:
    instance = PFindingClassificationsDjango.sync_from_ddict(
        p_finding_classifications_fixture.ddict
    )
    instance.refresh_from_db()
    return instance


@pytest.fixture()
def django_populated_p_finding_classifications_fixture(
    django_p_finding_classifications_fixture: PFindingClassificationsDjango,
    django_populated_p_finding_classification_choice_fixture: "PFindingClassificationChoiceDjango",
) -> PFindingClassificationsDjango:
    django_p_finding_classifications_fixture.refresh_from_db()
    # assert that finding classification choices is linked
    all_classification_choices = django_p_finding_classifications_fixture.patient_finding_classification_choices.all()
    # print(f"Linked classification choices: {all_classification_choices}")
    # check if django_p_finding_classification_choice_fixture is in all_classification_choices
    if (
        django_populated_p_finding_classification_choice_fixture
        not in all_classification_choices
    ):
        raise ValueError(
            "The django_p_finding_classification_choice_fixture is not linked to the django_p_finding_classifications_fixture."
        )
    return django_p_finding_classifications_fixture
