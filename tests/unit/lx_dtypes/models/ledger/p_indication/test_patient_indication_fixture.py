import pytest

from lx_dtypes.models.knowledge_base.indication.IndicationDjango import IndicationDjango
from lx_dtypes.models.ledger.p_indication.Django import PIndicationDjango
from lx_dtypes.models.ledger.p_indication.Pydantic import PIndication
from lx_dtypes.utils.testing import validate_django_fixture
from tests.paths import GENERATED_TEST_OUTPUT_ROOT


@pytest.mark.django_db
class TestPIndicationFixtures:
    def test_p_indication_fixture(self, p_indication_fixture: PIndication) -> None:
        assert p_indication_fixture is not None
        ddict = p_indication_fixture.ddict
        new_obj = p_indication_fixture.model_validate(ddict)
        new_ddict = new_obj.ddict

        # test validation function
        assert p_indication_fixture.validate_ddict(new_obj.model_dump()) is True

        assert ddict == new_ddict

        p_indication_fixture.to_yaml(
            GENERATED_TEST_OUTPUT_ROOT / "p_indication_fixture.yaml"
        )


@pytest.mark.django_db
class TestDjangoPIndicationFixture:
    def test_django_p_indication_fixture(
        self,
        django_indication_fixture: IndicationDjango,
        django_p_indication_fixture: PIndicationDjango,
    ) -> None:
        assert django_p_indication_fixture is not None

        validate_django_fixture(django_p_indication_fixture)
