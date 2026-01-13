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
        assert django_p_finding_fixture is not None

        validate_django_fixture(django_p_finding_fixture)
