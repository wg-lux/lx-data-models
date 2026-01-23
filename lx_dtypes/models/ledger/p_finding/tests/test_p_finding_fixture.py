from pathlib import Path

import pytest

from lx_dtypes.models.knowledge_base.finding._FindingDjango import (
    FindingDjango,
)
from lx_dtypes.utils.testing import validate_django_fixture

from ..Django import PFindingDjango
from ..Pydantic import PFinding


@pytest.mark.django_db
class TestPFindingFixtures:
    def test_p_finding_fixture(self, p_finding_fixture: PFinding) -> None:
        """
        Validate a PFinding fixture's serialization, validation, and YAML export.

        Asserts the provided PFinding fixture is present, that its dict form round-trips through model validation and produces an identical ddict, that `validate_ddict` accepts the serialized model, and exports the fixture to `p_finding_fixture.yaml` in the same directory as this test.

        Parameters:
            p_finding_fixture (PFinding): PFinding fixture instance to validate and export.
        """
        assert p_finding_fixture is not None
        ddict = p_finding_fixture.ddict
        new_obj = p_finding_fixture.model_validate(ddict)
        new_ddict = new_obj.ddict

        # test validation function
        assert p_finding_fixture.validate_ddict(new_obj.model_dump()) is True

        assert ddict == new_ddict

        p_finding_fixture.to_yaml(Path(__file__).parent / "p_finding_fixture.yaml")


@pytest.mark.django_db
class TestDjangoPFindingFixture:
    def test_django_p_finding_fixture(
        self,
        django_finding_fixture: FindingDjango,
        django_p_finding_fixture: PFindingDjango,
    ) -> None:
        """
        Validate the PFindingDjango fixture against Django expectations.

        Parameters:
            django_finding_fixture (FindingDjango): A FindingDjango fixture used to provide related data/setup for the test.
            django_p_finding_fixture (PFindingDjango): The PFindingDjango fixture to validate using framework checks.
        """
        assert django_p_finding_fixture is not None

        validate_django_fixture(django_p_finding_fixture)

    def test_populated_django_p_finding_fixture(
        self,
        django_populated_p_finding_fixture: PFindingDjango,
        django_finding_fixture: FindingDjango,
    ) -> None:
        """
        Validate a populated PFindingDjango fixture by converting it to a PFinding and exporting its serialized form to YAML.

        Parameters:
            django_populated_p_finding_fixture (PFindingDjango): Populated Django-backed PFinding fixture whose ddict will be validated and exported.
            django_finding_fixture (FindingDjango): Related FindingDjango fixture (provided by the test environment).
        """
        assert django_populated_p_finding_fixture is not None

        _ddict = django_populated_p_finding_fixture.ddict

        pydantic_instance = PFinding.model_validate(_ddict)

        pydantic_instance.to_yaml(
            Path(__file__).parent / "populated_p_finding_fixture.yaml"
        )
        validate_django_fixture(django_populated_p_finding_fixture)
