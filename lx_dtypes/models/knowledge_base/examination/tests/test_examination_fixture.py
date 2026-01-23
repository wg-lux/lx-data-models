from pathlib import Path

import pytest

from lx_dtypes.utils.ddict_schema import dump_ddict_schema
from lx_dtypes.utils.testing import validate_django_fixture

from ..Examination import Examination
from ..ExaminationDjango import ExaminationDjango
from ..ExaminationType import ExaminationType

TEST_EXPORT = Path(__file__).parent / "examination_fixture.yaml"
TEST_EXPORT_DDICT_SCHEMA = Path(__file__).parent / "examination_ddict_schema.yaml"


@pytest.mark.django_db
class TestDjangoExaminationFixture:
    def test_django_examination_fixture(
        self, django_examination_fixture: "ExaminationDjango"
    ) -> None:
        """
        Validate a Django-backed Examination fixture for structural and relational integrity.
        
        Uses the shared validate_django_fixture helper on the provided django_examination_fixture to assert the fixture's correctness.
        """
        validate_django_fixture(django_examination_fixture)


class TestExaminationTypeFixture:
    def test_examination_type_fixture(
        self, examination_type_fixture: ExaminationType
    ) -> None:
        """
        Verify that an ExaminationType fixture round-trips its data-dict, validates its dumped model, and can be exported to YAML.
        
        Parameters:
            examination_type_fixture (ExaminationType): Fixture instance representing an ExaminationType used for testing; its `ddict` is validated by creating a new model from the ddict, asserting the new model's dumped ddict equals the original, asserting the fixture's `validate_ddict` accepts the dumped model, and exporting the fixture to `examination_type_fixture.yaml`.
        """
        assert examination_type_fixture is not None
        ddict = examination_type_fixture.ddict
        new_obj = examination_type_fixture.model_validate(ddict)
        new_ddict = new_obj.ddict

        # test validation function
        assert examination_type_fixture.validate_ddict(new_obj.model_dump()) is True

        assert ddict == new_ddict

        # Test export to YAML
        examination_type_fixture.to_yaml(
            Path(__file__).parent / "examination_type_fixture.yaml"
        )

    def test_dump_examination_type_ddict(
        self, examination_type_fixture: ExaminationType
    ) -> None:
        """
        Export the ddict schema for the provided ExaminationType fixture to a YAML file.
        
        Dumps the fixture's `ddict_class` schema to `examination_type_ddict_schema.yaml` located in the same directory as this test module.
        
        Parameters:
            examination_type_fixture (ExaminationType): Fixture providing the `ddict_class` to be dumped.
        """
        ddict_type = examination_type_fixture.ddict_class
        dump_ddict_schema(
            ddict_type,
            Path(__file__).parent / "examination_type_ddict_schema.yaml",
        )


class TestExaminationFixture:
    def test_examination_fixture(self, examination_fixture: Examination) -> None:
        assert examination_fixture is not None
        ddict = examination_fixture.ddict
        new_obj = Examination.model_validate(ddict)
        new_ddict = new_obj.ddict

        # test validation function
        assert Examination.validate_ddict(new_obj.model_dump()) is True

        assert ddict == new_ddict

        # Test export to YAML
        examination_fixture.to_yaml(TEST_EXPORT)

    def test_dump_examination_ddict(self, examination_fixture: Examination) -> None:
        """
        Export the Examination data-dict (ddict) schema for the provided fixture to the module's test YAML path.
        
        Parameters:
            examination_fixture (Examination): Fixture providing the Examination ddict class whose schema will be dumped to TEST_EXPORT_DDICT_SCHEMA.
        """
        ddict_type = examination_fixture.ddict_class
        dump_ddict_schema(ddict_type, TEST_EXPORT_DDICT_SCHEMA)