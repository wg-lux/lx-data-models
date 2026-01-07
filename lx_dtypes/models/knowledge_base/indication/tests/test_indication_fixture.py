from pathlib import Path

from lx_dtypes.utils.ddict_schema import dump_ddict_schema

from ..Indication import Indication
from ..IndicationType import IndicationType

TEST_EXPORT = Path(__file__).parent / "indication_fixture.yaml"
TEST_EXPORT_DDICT_SCHEMA = Path(__file__).parent / "indication_ddict_schema.yaml"


class TestIndicationFixture:
    def test_indication_fixture(self, indication_fixture: Indication) -> None:
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
        ddict_type = indication_fixture.ddict_class
        dump_ddict_schema(ddict_type, TEST_EXPORT_DDICT_SCHEMA)


class TestIndicationTypeFixture:
    def test_indication_type_fixture(
        self, indication_type_fixture: IndicationType
    ) -> None:
        assert indication_type_fixture is not None
        ddict = indication_type_fixture.ddict
        new_obj = indication_type_fixture.model_validate(ddict)
        new_ddict = new_obj.ddict

        # test validation function
        assert indication_type_fixture.validate_ddict(new_obj.model_dump()) is True

        assert ddict == new_ddict

        # Test export to YAML
        indication_type_fixture.to_yaml(
            Path(__file__).parent / "indication_type_fixture.yaml"
        )

    def test_dump_indication_type_ddict(
        self, indication_type_fixture: IndicationType
    ) -> None:
        ddict_type = indication_type_fixture.ddict_class
        dump_ddict_schema(
            ddict_type,
            Path(__file__).parent / "indication_type_ddict_schema.yaml",
        )
