from pathlib import Path

from lx_dtypes.utils.ddict_schema import dump_ddict_schema

from ..Unit import Unit

TEST_EXPORT = Path(__file__).parent / "unit_fixture.yaml"
TEST_EXPORT_DDICT_SCHEMA = Path(__file__).parent / "unit_ddict_schema.yaml"


class TestUnitFixture:
    def test_unit_fixture(self, unit_fixture: Unit) -> None:
        assert unit_fixture is not None
        ddict = unit_fixture.ddict
        new_obj = Unit.model_validate(ddict)
        new_ddict = new_obj.ddict

        # test validation function
        assert Unit.validate_ddict(new_obj.model_dump()) is True

        assert ddict == new_ddict

        # Test export to YAML
        unit_fixture.to_yaml(TEST_EXPORT)

    def test_dump_unit_ddict(self, unit_fixture: Unit) -> None:
        ddict_type = unit_fixture.ddict_class
        dump_ddict_schema(ddict_type, TEST_EXPORT_DDICT_SCHEMA)
