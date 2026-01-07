from pathlib import Path

from lx_dtypes.utils.ddict_schema import dump_ddict_schema

from ..Examination import Examination
from ..ExaminationType import ExaminationType

TEST_EXPORT = Path(__file__).parent / "examination_fixture.yaml"
TEST_EXPORT_DDICT_SCHEMA = Path(__file__).parent / "examination_ddict_schema.yaml"


class TestExaminationTypeFixture:
    def test_examination_type_fixture(
        self, examination_type_fixture: ExaminationType
    ) -> None:
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
        ddict_type = examination_fixture.ddict_class
        dump_ddict_schema(ddict_type, TEST_EXPORT_DDICT_SCHEMA)
