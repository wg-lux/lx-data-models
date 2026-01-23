import pytest

from lx_dtypes.models.knowledge_base.classification_choice_descriptor.ClassificationChoiceDescriptorDjango import (
    ClassificationChoiceDescriptorDjango,
)

from ..Django import PFindingClassificationChoiceDescriptorDjango
from ..Pydantic import PFindingClassificationChoiceDescriptor


@pytest.fixture()
def p_finding_classification_choice_descriptor_fixture(
    django_classification_choice_descriptor_fixture: ClassificationChoiceDescriptorDjango,
    django_p_finding_classification_choice_fixture: PFindingClassificationChoiceDescriptorDjango,
) -> PFindingClassificationChoiceDescriptor:
    instance = PFindingClassificationChoiceDescriptor(
        descriptor_value=True,
        classification_choice_descriptor=str(
            django_classification_choice_descriptor_fixture.pk
        ),
        patient_finding_classification_choice=str(
            django_p_finding_classification_choice_fixture.pk
        ),
    )

    return instance


@pytest.fixture()
def django_p_finding_classification_choice_descriptor_fixture(
    p_finding_classification_choice_descriptor_fixture: PFindingClassificationChoiceDescriptor,
) -> PFindingClassificationChoiceDescriptorDjango:
    instance = PFindingClassificationChoiceDescriptorDjango.sync_from_ddict(
        p_finding_classification_choice_descriptor_fixture.ddict
    )
    instance.refresh_from_db()
    return instance
