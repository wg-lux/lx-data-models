import pytest

from lx_dtypes.models.knowledge_base.finding._Finding import Finding
from lx_dtypes.models.knowledge_base.finding._FindingDjango import FindingDjango
from lx_dtypes.models.knowledge_base.finding._FindingType import FindingType
from lx_dtypes.utils.ddict_schema import dump_ddict_schema
from lx_dtypes.utils.testing import validate_django_fixture
from tests.paths import GENERATED_TEST_OUTPUT_ROOT

TEST_EXPORT = GENERATED_TEST_OUTPUT_ROOT / "finding_fixture.yaml"
TEST_EXPORT_DDICT_SCHEMA = GENERATED_TEST_OUTPUT_ROOT / "finding_ddict_schema.yaml"


@pytest.mark.django_db
class TestDjangoFindingFixture:
    def test_django_finding_fixture(
        self, django_finding_fixture: "FindingDjango"
    ) -> None:
        """
        Validate the provided Django Finding fixture.

        Runs validation against the given Django fixture to ensure its serialized representation and the database-backed object are consistent.

        Parameters:
            django_finding_fixture (FindingDjango): Pytest fixture providing a Django model instance (and its serialized data) representing a Finding.
        """
        validate_django_fixture(django_finding_fixture)


class TestFindingFixture:
    def test_finding_fixture(self, finding_fixture: Finding) -> None:
        """
        Verify a Finding fixture round-trips through model validation, preserves its ddict, and can be exported to YAML.

        This test constructs a new Finding from the fixture's ddict, ensures the reconstructed object's ddict equals the original, validates the reconstructed model's dumped data with Finding.validate_ddict, and writes the fixture to TEST_EXPORT.

        Parameters:
            finding_fixture (Finding): The Finding test fixture to validate and export.
        """
        assert finding_fixture is not None
        ddict = finding_fixture.ddict
        new_obj = Finding.model_validate(ddict)
        new_ddict = new_obj.ddict

        # test validation function
        assert Finding.validate_ddict(new_obj.model_dump()) is True

        assert ddict == new_ddict

        # Test export to YAML
        finding_fixture.to_yaml(TEST_EXPORT)

    def test_dump_finding_ddict(self, finding_fixture: Finding) -> None:
        """
        Write the DDIC schema for the Finding fixture's ddict type to TEST_EXPORT_DDICT_SCHEMA.

        Parameters:
            finding_fixture (Finding): Test fixture whose `ddict_class` is used as the schema source.
        """
        ddict_type = finding_fixture.ddict_class
        dump_ddict_schema(ddict_type, TEST_EXPORT_DDICT_SCHEMA)


class TestFindingTypeFixture:
    def test_finding_type_fixture(self, finding_type_fixture: "FindingType") -> None:
        """
        Verify a FindingType fixture round-trips through validation and can be exported to YAML.

        Validates that a FindingType fixture:
        - can be used to construct a new instance from its ddict and produce an identical ddict,
        - passes the class-level ddict validation on the dumped model,
        - and can be exported to a YAML file named `finding_type_fixture.yaml` next to this test file.

        Parameters:
            finding_type_fixture (FindingType): Pytest fixture providing a populated FindingType instance.
        """
        assert finding_type_fixture is not None
        ddict = finding_type_fixture.ddict
        new_obj = finding_type_fixture.model_validate(ddict)
        new_ddict = new_obj.ddict

        # test validation function
        assert finding_type_fixture.validate_ddict(new_obj.model_dump()) is True

        assert ddict == new_ddict

        # Test export to YAML
        finding_type_fixture.to_yaml(
            GENERATED_TEST_OUTPUT_ROOT / "finding_type_fixture.yaml"
        )

    def test_dump_finding_type_ddict(self, finding_type_fixture: "FindingType") -> None:
        ddict_type = finding_type_fixture.ddict_class
        dump_ddict_schema(
            ddict_type,
            GENERATED_TEST_OUTPUT_ROOT / "finding_type_ddict_schema.yaml",
        )
