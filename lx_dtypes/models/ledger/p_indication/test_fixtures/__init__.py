import pytest

from lx_dtypes.models.knowledge_base.indication.IndicationDjango import IndicationDjango
from lx_dtypes.models.ledger.p_examination.Django import (
    PExaminationDjango,
)

from ..Django import PIndicationDjango
from ..Pydantic import PIndication


@pytest.fixture()
def p_indication_fixture(
    django_p_examination_fixture: PExaminationDjango,
    django_indication_fixture: IndicationDjango,
) -> PIndication:
    instance = PIndication(
        indication=django_indication_fixture.name,
        patient_examination=str(django_p_examination_fixture.pk),
    )
    return instance


@pytest.fixture()
def django_p_indication_fixture(
    p_indication_fixture: PIndication,
) -> PIndicationDjango:
    instance = PIndicationDjango.sync_from_ddict(p_indication_fixture.ddict)
    instance.refresh_from_db()
    return instance
