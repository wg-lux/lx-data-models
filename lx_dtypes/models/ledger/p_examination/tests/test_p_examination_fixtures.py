from pathlib import Path

import pytest

from lx_dtypes.models.ledger.p_finding.Django import PFindingDjango
from lx_dtypes.models.ledger.p_indication.Django import PIndicationDjango
from lx_dtypes.utils.testing import validate_django_fixture

from ..Django import PExaminationDjango
from ..Pydantic import PExamination


@pytest.mark.django_db
class TestPExaminationFixtures:
    def test_p_examination_fixture(self, p_examination_fixture: PExamination) -> None:
        assert p_examination_fixture is not None
        ddict = p_examination_fixture.ddict
        new_obj = p_examination_fixture.model_validate(ddict)
        new_ddict = new_obj.ddict

        # test validation function
        assert p_examination_fixture.validate_ddict(new_obj.model_dump()) is True

        assert ddict == new_ddict

        p_examination_fixture.to_yaml(
            Path(__file__).parent / "p_examination_fixture.yaml"
        )


@pytest.mark.django_db
class TestDjangoPExaminationFixture:
    def test_django_p_examination_fixture(
        self,
        django_p_examination_fixture: PExaminationDjango,
    ) -> None:
        assert django_p_examination_fixture is not None

        validate_django_fixture(django_p_examination_fixture)

    def test_populated_django_p_examination_fixture(
        self,
        django_populated_p_examination_fixture: PExaminationDjango,
        django_p_finding_fixture: PFindingDjango,
        django_p_indication_fixture: PIndicationDjango,
    ) -> None:
        assert django_populated_p_examination_fixture is not None

        _ddict = django_populated_p_examination_fixture.ddict
        for key, value in _ddict.items():
            print(f"{key}: {value}")
        pydantic_instance = PExamination.model_validate(_ddict)

        pydantic_instance.to_yaml(
            Path(__file__).parent / "populated_p_examination_fixture.yaml"
        )
        validate_django_fixture(django_populated_p_examination_fixture)
