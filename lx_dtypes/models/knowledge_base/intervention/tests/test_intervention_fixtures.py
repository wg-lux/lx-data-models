from pathlib import Path

import pytest

from lx_dtypes.utils.ddict_schema import dump_ddict_schema
from lx_dtypes.utils.testing import validate_django_fixture

from ..Intervention import Intervention
from ..InterventionDjango import InterventionDjango
from ..InterventionType import InterventionType

TEST_EXPORT = Path(__file__).parent / "intervention_fixture.yaml"
TEST_EXPORT_DDICT_SCHEMA = Path(__file__).parent / "intervention_ddict_schema.yaml"


class TestInterventionFixture:
    def test_intervention_fixture(self, intervention_fixture: Intervention) -> None:
        assert intervention_fixture is not None
        ddict = intervention_fixture.ddict
        new_obj = Intervention.model_validate(ddict)
        new_ddict = new_obj.ddict

        # test validation function
        assert Intervention.validate_ddict(new_obj.model_dump()) is True

        assert ddict == new_ddict

        # Test export to YAML
        intervention_fixture.to_yaml(TEST_EXPORT)

    def test_dump_intervention_ddict(self, intervention_fixture: Intervention) -> None:
        ddict_type = intervention_fixture.ddict_class
        dump_ddict_schema(ddict_type, TEST_EXPORT_DDICT_SCHEMA)


@pytest.mark.django_db
class TestDjangoInterventionFixture:
    def test_django_intervention_fixture(
        self, django_intervention_fixture: "InterventionDjango"
    ) -> None:
        validate_django_fixture(django_intervention_fixture)


class TestInterventionTypeFixture:
    def test_intervention_type_fixture(
        self, intervention_type_fixture: InterventionType
    ) -> None:
        assert intervention_type_fixture is not None
        ddict = intervention_type_fixture.ddict
        new_obj = InterventionType.model_validate(ddict)
        new_ddict = new_obj.ddict

        # test validation function
        assert InterventionType.validate_ddict(new_obj.model_dump()) is True

        assert ddict == new_ddict

        # Test export to YAML
        intervention_type_fixture.to_yaml(
            Path(__file__).parent / "intervention_type_fixture.yaml"
        )

    def test_dump_intervention_type_ddict(
        self, intervention_type_fixture: InterventionType
    ) -> None:
        ddict_type = intervention_type_fixture.ddict_class
        dump_ddict_schema(
            ddict_type,
            Path(__file__).parent / "intervention_type_ddict_schema.yaml",
        )
