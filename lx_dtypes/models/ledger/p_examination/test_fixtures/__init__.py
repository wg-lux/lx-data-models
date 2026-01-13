from datetime import datetime

import pytest

from lx_dtypes.models.knowledge_base.examination.ExaminationDjango import (
    ExaminationDjango,
)

from ..Django import PExaminationDjango
from ..Pydantic import PExamination


@pytest.fixture()
def p_examination_fixture(
    django_examination_fixture: ExaminationDjango,
) -> PExamination:
    instance = PExamination(
        examination=django_examination_fixture.name,
        date=datetime(2024, 1, 1, 10, 0, 0),
    )
    return instance


@pytest.fixture()
def django_p_examination_fixture(
    p_examination_fixture: PExamination,
    django_examination_fixture: ExaminationDjango,
) -> PExaminationDjango:
    instance = PExaminationDjango.sync_from_ddict(p_examination_fixture.ddict)
    instance.refresh_from_db()
    return instance
