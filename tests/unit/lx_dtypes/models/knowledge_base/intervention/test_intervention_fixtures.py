import pytest

from tests.paths import GENERATED_TEST_OUTPUT_ROOT

from lx_dtypes.utils.ddict_schema import dump_ddict_schema
from lx_dtypes.utils.testing import validate_django_fixture

from lx_dtypes.models.knowledge_base.intervention.Intervention import Intervention
from lx_dtypes.models.knowledge_base.intervention.InterventionDjango import (
    InterventionDjango,
)
from lx_dtypes.models.knowledge_base.intervention.InterventionType import (
    InterventionType,
)

TEST_EXPORT = GENERATED_TEST_OUTPUT_ROOT / "intervention_fixture.yaml"
TEST_EXPORT_DDICT_SCHEMA = GENERATED_TEST_OUTPUT_ROOT / "intervention_ddict_schema.yaml"


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
        """
        Dump the DDict schema for the provided Intervention fixture's ddict class to TEST_EXPORT_DDICT_SCHEMA.

        Parameters:
            intervention_fixture (Intervention): Fixture instance whose `ddict_class` will be used to generate and write the DDict schema.
        """
        ddict_type = intervention_fixture.ddict_class
        dump_ddict_schema(ddict_type, TEST_EXPORT_DDICT_SCHEMA)


@pytest.mark.django_db
class TestDjangoInterventionFixture:
    def test_django_intervention_fixture(
        self, django_intervention_fixture: "InterventionDjango"
    ) -> None:
        """
        Validate that the provided Django-backed Intervention fixture is a well-formed and usable fixture.

        Parameters:
            django_intervention_fixture (InterventionDjango): A Django model-backed Intervention fixture instance to validate.
        """
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
            GENERATED_TEST_OUTPUT_ROOT / "intervention_type_fixture.yaml"
        )

    def test_dump_intervention_type_ddict(
        self, intervention_type_fixture: InterventionType
    ) -> None:
        """
        Dumps the DDict schema of the provided InterventionType fixture to a YAML file next to this test.

        Parameters:
            intervention_type_fixture (InterventionType): Fixture whose `ddict_class` will be serialized into a DDict schema and written to `intervention_type_ddict_schema.yaml`.
        """
        ddict_type = intervention_type_fixture.ddict_class
        dump_ddict_schema(
            ddict_type,
            GENERATED_TEST_OUTPUT_ROOT / "intervention_type_ddict_schema.yaml",
        )
