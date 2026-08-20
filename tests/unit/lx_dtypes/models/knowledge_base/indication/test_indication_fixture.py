import pytest

from tests.paths import GENERATED_TEST_OUTPUT_ROOT

from lx_dtypes.utils.ddict_schema import dump_ddict_schema
from lx_dtypes.utils.testing import validate_django_fixture

from lx_dtypes.models.knowledge_base.indication.Indication import Indication
from lx_dtypes.models.knowledge_base.indication.IndicationDjango import IndicationDjango
from lx_dtypes.models.knowledge_base.indication.IndicationType import IndicationType

TEST_EXPORT = GENERATED_TEST_OUTPUT_ROOT / "indication_fixture.yaml"
TEST_EXPORT_DDICT_SCHEMA = GENERATED_TEST_OUTPUT_ROOT / "indication_ddict_schema.yaml"


class TestIndicationFixture:
    def test_indication_fixture(self, indication_fixture: Indication) -> None:
        """
        Verify an Indication fixture round-trips through its ddict representation, passes ddict validation, and can be exported to YAML.

        Asserts the fixture is present, that validating and reconstructing from its ddict yields an equivalent ddict, and that the fixture can be written to the TEST_EXPORT YAML path.
        """
        assert indication_fixture is not None
        ddict = indication_fixture.ddict
        new_obj = Indication.model_validate(ddict)
        new_ddict = new_obj.ddict

        # test validation function
        assert Indication.validate_ddict(new_obj.model_dump()) is True

        assert ddict == new_ddict

        # Test export to YAML
        indication_fixture.to_yaml(TEST_EXPORT)

    def test_dump_indication_ddict(self, indication_fixture: Indication) -> None:
        """
        Emit the ddict schema for the fixture's ddict class to the TEST_EXPORT_DDICT_SCHEMA file.

        Parameters:
            indication_fixture (Indication): Fixture providing the `ddict_class` whose DDIC schema will be written to TEST_EXPORT_DDICT_SCHEMA.
        """
        ddict_type = indication_fixture.ddict_class
        dump_ddict_schema(ddict_type, TEST_EXPORT_DDICT_SCHEMA)


@pytest.mark.django_db
class TestDjangoIndicationFixture:
    def test_django_indication_fixture(
        self, django_indication_fixture: "IndicationDjango"
    ) -> None:
        """
        Validate a Django-backed Indication fixture.

        Parameters:
            django_indication_fixture (IndicationDjango): A Django model fixture for an Indication to be validated by the test.
        """
        validate_django_fixture(django_indication_fixture)


class TestIndicationTypeFixture:
    def test_indication_type_fixture(
        self, indication_type_fixture: IndicationType
    ) -> None:
        """
        Validate an IndicationType fixture's ddict round-trip, validation, equality, and YAML export.

        This test ensures the provided fixture can be reconstructed from its ddict, that the reconstructed
        object's ddict matches the original, that `validate_ddict` succeeds on the reconstructed object's
        dump, and that the fixture can be exported to a file named `indication_type_fixture.yaml`
        next to the test file.

        Parameters:
            indication_type_fixture (IndicationType): Fixture instance to validate and export.
        """
        assert indication_type_fixture is not None
        ddict = indication_type_fixture.ddict
        new_obj = indication_type_fixture.model_validate(ddict)
        new_ddict = new_obj.ddict

        # test validation function
        assert indication_type_fixture.validate_ddict(new_obj.model_dump()) is True

        assert ddict == new_ddict

        # Test export to YAML
        indication_type_fixture.to_yaml(
            GENERATED_TEST_OUTPUT_ROOT / "indication_type_fixture.yaml"
        )

    def test_dump_indication_type_ddict(
        self, indication_type_fixture: IndicationType
    ) -> None:
        """
        Emit the DDIC schema for an IndicationType fixture to a YAML file.

        Parameters:
            indication_type_fixture (IndicationType): Fixture whose `ddict_class` will be used to generate and write the DDIC schema to the file `indication_type_ddict_schema.yaml` located next to this test module.
        """
        ddict_type = indication_type_fixture.ddict_class
        dump_ddict_schema(
            ddict_type,
            GENERATED_TEST_OUTPUT_ROOT / "indication_type_ddict_schema.yaml",
        )
