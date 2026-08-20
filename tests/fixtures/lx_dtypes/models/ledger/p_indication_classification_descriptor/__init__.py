import pytest

from lx_dtypes.models.knowledge_base.classification_choice_descriptor.ClassificationChoiceDescriptorDjango import (
    ClassificationChoiceDescriptorDjango,
)
from lx_dtypes.models.ledger.p_indication_classification.Django import (
    PIndicationClassificationDjango,
)

from lx_dtypes.models.ledger.p_indication_classification_descriptor.Django import (
    PIndicationClassificationDescriptorDjango,
)
from lx_dtypes.models.ledger.p_indication_classification_descriptor.Pydantic import (
    PIndicationClassificationDescriptor,
)


@pytest.fixture()
def p_indication_classification_descriptor_fixture(
    django_p_indication_classification_fixture: PIndicationClassificationDjango,
    django_classification_choice_descriptor_fixture: ClassificationChoiceDescriptorDjango,
) -> PIndicationClassificationDescriptor:
    return PIndicationClassificationDescriptor(
        descriptor_value="12",
        classification_choice_descriptor=str(
            django_classification_choice_descriptor_fixture.pk
        ),
        patient_indication_classification=str(
            django_p_indication_classification_fixture.pk
        ),
    )


@pytest.fixture()
def django_p_indication_classification_descriptor_fixture(
    p_indication_classification_descriptor_fixture: PIndicationClassificationDescriptor,
) -> PIndicationClassificationDescriptorDjango:
    instance = PIndicationClassificationDescriptorDjango.sync_from_ddict(
        p_indication_classification_descriptor_fixture.ddict
    )
    instance.refresh_from_db()
    return instance
