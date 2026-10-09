import pytest

from lx_dtypes.models.knowledge_base.unit.Unit import Unit
from lx_dtypes.models.knowledge_base.unit.UnitDjango import UnitDjango
from lx_dtypes.utils.ddict_schema import dump_ddict_schema
from lx_dtypes.utils.testing import validate_django_fixture
from tests.paths import GENERATED_TEST_OUTPUT_ROOT

TEST_EXPORT = GENERATED_TEST_OUTPUT_ROOT / "unit_fixture.yaml"
TEST_EXPORT_DDICT_SCHEMA = GENERATED_TEST_OUTPUT_ROOT / "unit_ddict_schema.yaml"


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


@pytest.mark.django_db
class TestDjangoUnitFixture:
    def test_django_unit_fixture(self, django_unit_fixture: "UnitDjango") -> None:
        """
        Validate that the provided Django Unit fixture meets the test suite's expected fixture requirements.

        Parameters:
            django_unit_fixture (UnitDjango): A Django Unit model instance supplied by the test fixture, which will be validated for correctness and completeness.
        """
        validate_django_fixture(django_unit_fixture)
