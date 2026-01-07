from ..ClassificationChoiceDescriptor import ClassificationChoiceDescriptor


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
