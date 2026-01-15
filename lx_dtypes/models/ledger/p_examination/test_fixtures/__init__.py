from datetime import datetime

import pytest

from lx_dtypes.models.knowledge_base.examination.ExaminationDjango import (
    ExaminationDjango,
)
from lx_dtypes.models.ledger.p_finding.Django import PFindingDjango
from lx_dtypes.models.ledger.p_indication.Django import PIndicationDjango

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


@pytest.fixture()
def django_populated_p_examination_fixture(
    django_p_examination_fixture: PExaminationDjango,
    django_p_finding_fixture: PFindingDjango,
    django_p_indication_fixture: PIndicationDjango,
) -> PExaminationDjango:
    django_p_examination_fixture.refresh_from_db()

    # assert that finding is linked
    all_findings = django_p_examination_fixture.patient_findings.all()
    print(f"Linked findings: {all_findings}")
    # check if django_finding_fixture is in all_findings
    if django_p_finding_fixture not in all_findings:
        raise ValueError(
            "The django_finding_fixture is not linked to the django_p_examination_fixture."
        )

    all_indications = django_p_examination_fixture.patient_indications.all()

    print(f"Linked indications: {all_indications}")
    # check if django_indication_fixture is in all_indications
    if django_p_indication_fixture not in all_indications:
        raise ValueError(
            "The django_indication_fixture is not linked to the django_p_examination_fixture."
        )

    return django_p_examination_fixture
