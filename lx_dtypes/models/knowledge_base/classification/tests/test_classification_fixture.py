from pathlib import Path

import pytest

from lx_dtypes.utils.ddict_schema import dump_ddict_schema
from lx_dtypes.utils.testing import validate_django_fixture

from ..Classification import Classification
from .._ClassificationDjango import ClassificationDjango

TEST_EXPORT = Path(__file__).parent / "classification_fixture.yaml"
TEST_EXPORT_DDICT_SCHEMA = Path(__file__).parent / "classification_ddict_schema.yaml"


@pytest.mark.django_db
class TestDjangoClassificationFixture:
    def test_django_classification_fixture(
        self, django_classification_fixture: "ClassificationDjango"
    ) -> None:
        validate_django_fixture(django_classification_fixture)
        # Additional validation can be added here as needed


class TestClassificationFixture:
    def test_classification_fixture(
        self, classification_fixture: Classification
    ) -> None:
        """
        Validate a Classification fixture for ddict round-trip consistency and YAML export.
        
        Asserts the provided fixture is present, that constructing a new Classification from its ddict and dumping the model produces an equivalent ddict, and that the ddict passes Classification.validate_ddict. Finally, exports the fixture to the TEST_EXPORT YAML file.
        
        Parameters:
            classification_fixture (Classification): Fixture instance to validate and export.
        """
        assert classification_fixture is not None
        ddict = classification_fixture.ddict
        new_obj = Classification.model_validate(ddict)
        new_ddict = new_obj.ddict

        # test validation function
        assert Classification.validate_ddict(new_obj.model_dump()) is True

        assert ddict == new_ddict

        # Test export to YAML
        classification_fixture.to_yaml(TEST_EXPORT)

    def test_dump_classification_ddict(
        self, classification_fixture: Classification
    ) -> None:
        """
        Dump the ddict schema for the provided Classification fixture to the test export path.
        
        Parameters:
            classification_fixture (Classification): Fixture whose `ddict_class` will be exported to the file path defined by TEST_EXPORT_DDICT_SCHEMA.
        """
        ddict_type = classification_fixture.ddict_class
        dump_ddict_schema(ddict_type, TEST_EXPORT_DDICT_SCHEMA)