from pathlib import Path

import pytest

from lx_dtypes.utils.ddict_schema import dump_ddict_schema
from lx_dtypes.utils.testing import validate_django_fixture

from ..Finding import Finding
from ..FindingDjango import FindingDjango
from ..FindingType import FindingType

TEST_EXPORT = Path(__file__).parent / "finding_fixture.yaml"
TEST_EXPORT_DDICT_SCHEMA = Path(__file__).parent / "finding_ddict_schema.yaml"


@pytest.mark.django_db
class TestDjangoFindingFixture:
    def test_django_finding_fixture(
        self, django_finding_fixture: "FindingDjango"
    ) -> None:
        validate_django_fixture(django_finding_fixture)


class TestFindingFixture:
    def test_finding_fixture(self, finding_fixture: Finding) -> None:
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
        ddict_type = finding_fixture.ddict_class
        dump_ddict_schema(ddict_type, TEST_EXPORT_DDICT_SCHEMA)


class TestFindingTypeFixture:
    def test_finding_type_fixture(self, finding_type_fixture: "FindingType") -> None:
        assert finding_type_fixture is not None
        ddict = finding_type_fixture.ddict
        new_obj = finding_type_fixture.model_validate(ddict)
        new_ddict = new_obj.ddict

        # test validation function
        assert finding_type_fixture.validate_ddict(new_obj.model_dump()) is True

        assert ddict == new_ddict

        # Test export to YAML
        finding_type_fixture.to_yaml(
            Path(__file__).parent / "finding_type_fixture.yaml"
        )

    def test_dump_finding_type_ddict(self, finding_type_fixture: "FindingType") -> None:
        ddict_type = finding_type_fixture.ddict_class
        dump_ddict_schema(
            ddict_type,
            Path(__file__).parent / "finding_type_ddict_schema.yaml",
        )
