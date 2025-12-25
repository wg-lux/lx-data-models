from typing import Tuple

import pytest

from lx_dtypes.lx_django.models import (
    Center as DjangoCenterModel,
)
from lx_dtypes.lx_django.models import (
    Examiner as DjangoExaminerModel,
)
from lx_dtypes.lx_django.models import (
    Patient as DjangoPatientModel,
)
from lx_dtypes.lx_django.models.ledger.patient_examination import (
    PatientExamination as DjangoPatientExaminationModel,
)
from lx_dtypes.models.ledger.center import Center
from lx_dtypes.models.ledger.center_shallow import CenterShallow
from lx_dtypes.models.ledger.examiner import ExaminerShallow
from lx_dtypes.models.ledger.patient import Patient, PatientShallow
from lx_dtypes.models.ledger.patient_examination import PatientExamination


@pytest.mark.django_db
class TestLedgerModelSync:
    def test_patient_examination_sync(
        self,
        sample_patient_examination: PatientExamination,
        sample_django_patient_examination: DjangoPatientExaminationModel,
    ) -> None:
        pass

    def test_center_with_examiner_sync(
        self,
        sample_center_with_examiners: Center,
        sample_django_center_with_examiners: DjangoCenterModel,
    ) -> None:
        center_dict = sample_django_center_with_examiners.to_ddict_shallow()

        converted_center = CenterShallow.model_validate(center_dict)
        assert (
            converted_center.to_ddict_shallow()
            == sample_center_with_examiners.to_ddict_shallow()
        )

        # Validate examiners
        for examiner_uuid, examiner in sample_center_with_examiners.examiners.items():
            django_examiner = DjangoExaminerModel.objects.get(uuid=examiner_uuid)
            examiner_dict = django_examiner.to_ddict_shallow()
            converted_examiner = ExaminerShallow.model_validate(examiner_dict)
            assert converted_examiner.to_ddict_shallow() == examiner.to_ddict_shallow()

    def test_patient_sync(
        self,
        sample_patient_with_center: Tuple[Patient, Center],
        sample_django_patient_with_center: DjangoPatientModel,
    ) -> None:
        sample_patient, sample_center = sample_patient_with_center

        retrieved_patient = sample_django_patient_with_center
        assert str(retrieved_patient.uuid) == sample_patient.uuid
        patient_dict = retrieved_patient.to_ddict_shallow()

        converted_patient = PatientShallow.model_validate(patient_dict)
        assert converted_patient.to_ddict_shallow() == sample_patient.to_ddict_shallow()
