from pathlib import Path

import pytest

from lx_dtypes.utils.ddict_schema import dump_ddict_schema

from ..ClassificationChoice import ClassificationChoice
from ..ClassificationChoiceDjango import ClassificationChoiceDjango

TEST_EXPORT = Path(__file__).parent / "classification_choice_fixture.yaml"
TEST_EXPORT_DDICT_SCHEMA = (
    Path(__file__).parent / "classification_choice_ddict_schema.yaml"
)


@pytest.mark.django_db
class TestDjangoClassificationChoiceFixture:
    def test_django_classification_choice_fixture(
        self, django_classification_choice_fixture: "ClassificationChoiceDjango"
    ) -> None:
        assert django_classification_choice_fixture is not None
        # Additional validation can be added here as needed


class TestClassificationChoiceFixture:
    def test_invalid_dict_raises(self) -> None:
        invalid_dict = {
            "classification_choice_descriptors": "valid_string",
            "invalid_field": 123,
        }
        try:
            ClassificationChoice.validate_ddict(invalid_dict)
        except ValueError as e:
            assert "Invalid DataDict" in str(e)

        return None

    def test_invalid_class_instance_raises(self) -> None:
        try:
            _invalid_instance = ClassificationChoice(  # type: ignore
                classification_choice_descriptors="valid_string"
            )

        except ValueError as e:
            assert "name" in str(e)
            assert "Field required" in str(e)

    def test_serialize_str_fields(
        self, classification_choice_fixture: ClassificationChoice
    ) -> None:
        ddict = classification_choice_fixture.ddict
        assert isinstance(ddict["classification_choice_descriptors"], str)
        assert ddict["classification_choice_descriptors"] == "Sample Descriptor"
        assert ddict["tags"] == "tag1,tag2"

    def test_classification_choice_fixture(
        self, classification_choice_fixture: ClassificationChoice
    ) -> None:
        assert classification_choice_fixture is not None
        ddict = classification_choice_fixture.ddict
        new_obj = ClassificationChoice.model_validate(ddict)
        new_ddict = new_obj.ddict

        # test validation function
        assert ClassificationChoice.validate_ddict(new_obj.model_dump()) is True
        assert ddict == new_ddict

        # Test export to YAML
        classification_choice_fixture.to_yaml(TEST_EXPORT)

    def test_dump_classification_choice_ddict(
        self, classification_choice_fixture: ClassificationChoice
    ) -> None:
        ddict_type = classification_choice_fixture.ddict_class
        dump_ddict_schema(ddict_type, TEST_EXPORT_DDICT_SCHEMA)
