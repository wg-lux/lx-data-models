from datetime import datetime, timezone

import pytest

from lx_dtypes.models.ledger.center.Django import CenterDjango

from ..Django import PatientDjango


@pytest.fixture()
def patient_fixture(
    django_center_fixture: CenterDjango,
) -> PatientDjango:
    instance = PatientDjango(
        center=django_center_fixture, dob=datetime(1990, 1, 1, tzinfo=timezone.utc)
    )
    instance.save()
    return instance


@pytest.fixture()
def django_patient_fixture(
    patient_fixture: PatientDjango,
) -> PatientDjango:
    patient_django = PatientDjango.sync_from_ddict(patient_fixture.ddict)
    patient_django.refresh_from_db()

    return patient_django
