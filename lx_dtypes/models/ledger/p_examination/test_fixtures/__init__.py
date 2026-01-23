from datetime import datetime, timezone

import pytest

from lx_dtypes.models.knowledge_base.examination.ExaminationDjango import (
    ExaminationDjango,
)
from lx_dtypes.models.ledger.p_finding.Django import PFindingDjango
from lx_dtypes.models.ledger.p_indication.Django import PIndicationDjango
from lx_dtypes.models.ledger.patient.Django import PatientDjango

from ..Django import PExaminationDjango
from ..Pydantic import PExamination


@pytest.fixture()
def p_examination_fixture(
    django_examination_fixture: ExaminationDjango,
    django_patient_fixture: PatientDjango,
) -> PExamination:
    """
    Create a PExamination test instance using the provided Django fixtures and a fixed UTC datetime.

    Parameters:
        django_examination_fixture (ExaminationDjango): Django Examination whose `name` is used for the `examination` field.
        django_patient_fixture (PatientDjango): Django Patient whose primary key is used (as a string) for the `patient` field.

    Returns:
        PExamination: Instance with `patient` set to the patient's PK string, `examination` set to the examination name, and `date` set to 2024-01-01T10:00:00Z.
    """
    instance = PExamination(
        patient=str(django_patient_fixture.pk),
        examination=django_examination_fixture.name,
        date=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
    )
    return instance


@pytest.fixture()
def django_p_examination_fixture(
    p_examination_fixture: PExamination,
    django_examination_fixture: ExaminationDjango,
) -> PExaminationDjango:
    """
    Create a PExaminationDjango instance from a PExamination fixture and return it with database state refreshed.

    Parameters:
        p_examination_fixture (PExamination): Pydantic representation used to create or update the Django instance.
        django_examination_fixture (ExaminationDjango): Provided to ensure the Examination Django fixture is available for test dependency wiring.

    Returns:
        PExaminationDjango: The Django model instance corresponding to `p_examination_fixture`, refreshed from the database.
    """
    instance = PExaminationDjango.sync_from_ddict(p_examination_fixture.ddict)
    instance.refresh_from_db()
    return instance


@pytest.fixture()
def django_populated_p_examination_fixture(
    django_p_examination_fixture: PExaminationDjango,
    django_p_finding_fixture: PFindingDjango,
    django_p_indication_fixture: PIndicationDjango,
) -> PExaminationDjango:
    """
    Validate that a PExaminationDjango has the expected related finding and indication, then return it.

    Parameters:
        django_p_examination_fixture (PExaminationDjango): The examination Django instance to refresh and validate.
        django_p_finding_fixture (PFindingDjango): The expected finding instance that should be linked to the examination.
        django_p_indication_fixture (PIndicationDjango): The expected indication instance that should be linked to the examination.

    Returns:
        PExaminationDjango: The same `django_p_examination_fixture` after validation.

    Raises:
        ValueError: If `django_p_finding_fixture` is not present in the examination's `patient_findings` or
                    if `django_p_indication_fixture` is not present in the examination's `patient_indications`.
    """
    django_p_examination_fixture.refresh_from_db()

    # assert that finding is linked
    all_findings = django_p_examination_fixture.patient_findings.all()
    # check if django_finding_fixture is in all_findings
    if django_p_finding_fixture not in all_findings:
        raise ValueError(
            "The django_finding_fixture is not linked to the django_p_examination_fixture."
        )

    all_indications = django_p_examination_fixture.patient_indications.all()

    # check if django_indication_fixture is in all_indications
    if django_p_indication_fixture not in all_indications:
        raise ValueError(
            "The django_indication_fixture is not linked to the django_p_examination_fixture."
        )

    return django_p_examination_fixture
