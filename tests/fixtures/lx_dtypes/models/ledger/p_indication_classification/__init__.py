import pytest

from lx_dtypes.models.knowledge_base.classification._ClassificationDjango import (
    ClassificationDjango,
)
from lx_dtypes.models.knowledge_base.classification_choice.ClassificationChoiceDjango import (
    ClassificationChoiceDjango,
)
from lx_dtypes.models.ledger.p_indication.Django import PIndicationDjango
from lx_dtypes.models.ledger.p_indication_classification_descriptor.Django import (
    PIndicationClassificationDescriptorDjango,
)

from lx_dtypes.models.ledger.p_indication_classification.Django import (
    PIndicationClassificationDjango,
)
from lx_dtypes.models.ledger.p_indication_classification.Pydantic import (
    PIndicationClassification,
)


@pytest.fixture()
def p_indication_classification_fixture(
    django_p_indication_fixture: PIndicationDjango,
    django_classification_fixture: ClassificationDjango,
    django_classification_choice_fixture: ClassificationChoiceDjango,
) -> PIndicationClassification:
    return PIndicationClassification(
        classification=str(django_classification_fixture.pk),
        classification_choice=str(django_classification_choice_fixture.pk),
        patient_indication=str(django_p_indication_fixture.pk),
    )


@pytest.fixture()
def django_p_indication_classification_fixture(
    p_indication_classification_fixture: PIndicationClassification,
) -> PIndicationClassificationDjango:
    instance = PIndicationClassificationDjango.sync_from_ddict(
        p_indication_classification_fixture.ddict
    )
    instance.refresh_from_db()
    return instance


@pytest.fixture()
def django_populated_p_indication_classification_fixture(
    django_p_indication_classification_fixture: PIndicationClassificationDjango,
    django_p_indication_classification_descriptor_fixture: (
        PIndicationClassificationDescriptorDjango
    ),
) -> PIndicationClassificationDjango:
    django_p_indication_classification_fixture.refresh_from_db()
    all_descriptors = django_p_indication_classification_fixture.patient_indication_classification_descriptors.all()

    if django_p_indication_classification_descriptor_fixture not in all_descriptors:
        raise ValueError(
            "The django_p_indication_classification_descriptor_fixture is not linked "
            "to the django_p_indication_classification_fixture."
        )

    return django_p_indication_classification_fixture
