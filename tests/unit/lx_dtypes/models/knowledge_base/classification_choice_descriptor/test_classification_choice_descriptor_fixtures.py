import pytest

from lx_dtypes.utils.testing import validate_django_fixture

from lx_dtypes.models.knowledge_base.classification_choice_descriptor.ClassificationChoiceDescriptor import (
    ClassificationChoiceDescriptor,
)
from lx_dtypes.models.knowledge_base.classification_choice_descriptor.ClassificationChoiceDescriptorDjango import (
    ClassificationChoiceDescriptorDjango,
)


class TestClassificationChoiceDescriptor:
    def test_descriptor_fixture(
        self, classification_choice_descriptor_fixture: ClassificationChoiceDescriptor
    ) -> None:
        assert isinstance(
            classification_choice_descriptor_fixture, ClassificationChoiceDescriptor
        )

        classification_choice_descriptor_ddict = (
            classification_choice_descriptor_fixture.ddict
        )
        _uuid = classification_choice_descriptor_ddict["uuid"]
        assert isinstance(_uuid, str)


@pytest.mark.django_db
class TestDjangoClassificationChoiceDescriptor:
    def test_django_descriptor_fixture(
        self,
        django_classification_choice_descriptor_fixture: "ClassificationChoiceDescriptorDjango",
    ) -> None:
        validate_django_fixture(django_classification_choice_descriptor_fixture)
