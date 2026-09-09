import pytest

from lx_dtypes.models.knowledge_base.classification_choice.ClassificationChoice import (
    ClassificationChoice,
)
from lx_dtypes.models.knowledge_base.classification_choice.ClassificationChoiceDjango import (
    ClassificationChoiceDjango,
)
from lx_dtypes.utils.ddict_schema import dump_ddict_schema
from tests.paths import GENERATED_TEST_OUTPUT_ROOT

TEST_EXPORT = GENERATED_TEST_OUTPUT_ROOT / "classification_choice_fixture.yaml"
TEST_EXPORT_DDICT_SCHEMA = (
    GENERATED_TEST_OUTPUT_ROOT / "classification_choice_ddict_schema.yaml"
)


@pytest.mark.django_db
class TestDjangoClassificationChoiceFixture:
    def test_django_classification_choice_fixture(
        self, django_classification_choice_fixture: "ClassificationChoiceDjango"
    ) -> None:
        """
        Verify that the Django-backed ClassificationChoice fixture is available.

        Parameters:
            django_classification_choice_fixture (ClassificationChoiceDjango): A pytest fixture providing a Django-backed ClassificationChoice instance used by the test.
        """
        assert django_classification_choice_fixture is not None
        # Additional validation can be added here as needed


class TestClassificationChoiceFixture:
    def test_invalid_dict_raises(self) -> None:
        """
        Verifies that validate_ddict raises a ValueError for dictionaries containing unexpected fields.

        Asserts the raised exception's message contains "Invalid DataDict".
        """
        invalid_dict = {
            "classification_choice_descriptors": "valid_string",
            "invalid_field": 123,
        }
        try:
            ClassificationChoice.validate_ddict(invalid_dict)
        except ValueError as e:
            assert "Invalid DataDict" in str(e)

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
        """
        Verify the fixture's ddict serializes specific fields with expected values.

        Parameters:
            classification_choice_fixture (ClassificationChoice): Fixture providing a ClassificationChoice whose `ddict` must contain `classification_choice_descriptors` equal to "Sample Descriptor" and `tags` equal to "tag1,tag2".
        """
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
        """
        Emit the data dictionary (DDict) schema for the fixture's classification choice.

        Parameters:
            classification_choice_fixture (ClassificationChoice): Fixture instance whose `ddict_class` will be exported as a DDict schema to the TEST_EXPORT_DDICT_SCHEMA path.
        """
        ddict_type = classification_choice_fixture.ddict_class
        dump_ddict_schema(ddict_type, TEST_EXPORT_DDICT_SCHEMA)
