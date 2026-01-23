from pathlib import Path

import pytest

from lx_dtypes.utils.ddict_schema import dump_ddict_schema
from lx_dtypes.utils.testing import validate_django_fixture

from ..Django import CenterDjango
from ..Pydantic import Center


@pytest.mark.django_db
class TestDjangoCenterFixture:
    def test_django_center_fixture(self, django_center_fixture: "CenterDjango") -> None:
        assert django_center_fixture is not None
        validate_django_fixture(django_center_fixture)


class TestCenterFixture:
    def test_center_fixture(self, center_fixture: Center) -> None:
        assert center_fixture is not None
        ddict = center_fixture.ddict
        new_obj = center_fixture.model_validate(ddict)
        new_ddict = new_obj.ddict

        # test validation function
        assert center_fixture.validate_ddict(new_obj.model_dump()) is True

        assert ddict == new_ddict

        # Test export to YAML
        center_fixture.to_yaml(Path(__file__).parent / "center_fixture.yaml")

    def test_dump_center_ddict(self, center_fixture: Center) -> None:
        """
        Dump the Center ddict schema to a YAML file adjacent to this test.
        
        Parameters:
            center_fixture (Center): A Center fixture whose `ddict_class` schema will be exported to `center_ddict_schema.yaml` in the same directory as this test.
        """
        ddict_type = center_fixture.ddict_class
        dump_ddict_schema(
            ddict_type,
            Path(__file__).parent / "center_ddict_schema.yaml",
        )