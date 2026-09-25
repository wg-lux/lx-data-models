import pytest

from lx_dtypes.models.ledger.p_indication_classification.Django import (
    PIndicationClassificationDjango,
)
from lx_dtypes.models.ledger.p_indication_classification.Pydantic import (
    PIndicationClassification,
)
from lx_dtypes.utils.testing import validate_django_fixture
from tests.paths import GENERATED_TEST_OUTPUT_ROOT


@pytest.mark.django_db
class TestPIndicationClassificationFixtures:
    def test_p_indication_classification_fixture(
        self,
        p_indication_classification_fixture: PIndicationClassification,
    ) -> None:
        assert p_indication_classification_fixture is not None
        ddict = p_indication_classification_fixture.ddict
        new_obj = p_indication_classification_fixture.model_validate(ddict)
        new_ddict = new_obj.ddict

        assert (
            p_indication_classification_fixture.validate_ddict(new_obj.model_dump())
            is True
        )
        assert ddict == new_ddict

        p_indication_classification_fixture.to_yaml(
            GENERATED_TEST_OUTPUT_ROOT / "p_indication_classification_fixture.yaml"
        )


@pytest.mark.django_db
class TestDjangoPIndicationClassificationFixture:
    def test_django_p_indication_classification_fixture(
        self,
        django_p_indication_classification_fixture: PIndicationClassificationDjango,
    ) -> None:
        validate_django_fixture(django_p_indication_classification_fixture)
