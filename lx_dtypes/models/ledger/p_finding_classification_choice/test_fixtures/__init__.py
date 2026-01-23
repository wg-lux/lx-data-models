import pytest

from lx_dtypes.models.knowledge_base.classification._ClassificationDjango import (
    ClassificationDjango,
)
from lx_dtypes.models.knowledge_base.classification_choice.ClassificationChoiceDjango import (
    ClassificationChoiceDjango,
)
from lx_dtypes.models.ledger.p_finding_classification_choice_descriptor.Django import (
    PFindingClassificationChoiceDescriptorDjango,
)
from lx_dtypes.models.ledger.p_finding_classifications.Django import (
    PFindingClassificationsDjango,
)

from ..Django import PFindingClassificationChoiceDjango
from ..Pydantic import PFindingClassificationChoice


@pytest.fixture()
def p_finding_classification_choice_fixture(
    django_p_finding_classifications_fixture: PFindingClassificationsDjango,
    django_classification_fixture: ClassificationDjango,
    django_classification_choice_fixture: ClassificationChoiceDjango,
) -> PFindingClassificationChoice:
    instance = PFindingClassificationChoice(
        classification=str(django_classification_fixture.pk),
        classification_choice=str(django_classification_choice_fixture.pk),
        patient_finding_classifications=str(
            django_p_finding_classifications_fixture.pk
        ),
    )
    return instance


@pytest.fixture()
def django_p_finding_classification_choice_fixture(
    p_finding_classification_choice_fixture: PFindingClassificationChoice,
) -> PFindingClassificationChoiceDjango:
    instance = PFindingClassificationChoiceDjango.sync_from_ddict(
        p_finding_classification_choice_fixture.ddict
    )
    instance.refresh_from_db()
    return instance


@pytest.fixture()
def django_populated_p_finding_classification_choice_fixture(
    django_p_finding_classification_choice_fixture: PFindingClassificationChoiceDjango,
    django_p_finding_classification_choice_descriptor_fixture: (
        "PFindingClassificationChoiceDescriptorDjango"
    ),
) -> PFindingClassificationChoiceDjango:
    django_p_finding_classification_choice_fixture.refresh_from_db()

    # assert that finding classification choice descriptors is linked
    all_descriptors = django_p_finding_classification_choice_fixture.patient_finding_classification_choice_descriptors.all()

    if django_p_finding_classification_choice_descriptor_fixture not in all_descriptors:
        raise ValueError(
            "The django_p_finding_classification_choice_descriptor_fixture is not linked to the django_p_finding_classification_choice_fixture."
        )

    return django_p_finding_classification_choice_fixture
