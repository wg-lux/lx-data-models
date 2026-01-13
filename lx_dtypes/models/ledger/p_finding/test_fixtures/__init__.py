from datetime import datetime

import pytest

from lx_dtypes.models.knowledge_base.finding._FindingDjango import (
    FindingDjango,
)
from lx_dtypes.models.ledger.p_examination.Django import (
    PExaminationDjango,
)

from ..Django import PFindingDjango
from ..Pydantic import PFinding


@pytest.fixture()
def p_finding_fixture(
    django_p_examination_fixture: PExaminationDjango,
    django_finding_fixture: "FindingDjango",
) -> PFinding:
    instance = PFinding(
        finding=django_finding_fixture.name,
        patient_examination=str(django_p_examination_fixture.pk),
    )
    return instance


@pytest.fixture()
def django_p_finding_fixture(
    p_finding_fixture: PFinding,
) -> PFindingDjango:
    instance = PFindingDjango.sync_from_ddict(p_finding_fixture.ddict)
    instance.refresh_from_db()
    return instance
