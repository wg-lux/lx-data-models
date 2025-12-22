from typing import Tuple

import pytest

from lx_dtypes.contrib.lx_django.models import (
    Center as DjangoCenterModel,
)
from lx_dtypes.contrib.lx_django.models import (
    Examiner as DjangoExaminerModel,
)
from lx_dtypes.contrib.lx_django.models import (
    Patient as DjangoPatientModel,
)
from lx_dtypes.models.ledger.center import Center
from lx_dtypes.models.ledger.center_shallow import CenterShallow
from lx_dtypes.models.ledger.examiner import ExaminerShallow
from lx_dtypes.models.ledger.patient import Patient, PatientShallow


@pytest.mark.django_db
class TestLedgerModelSync:
    def test_center_sync(self, sample_center_with_examiners: Center) -> None:
        ddict = sample_center_with_examiners.to_ddict()
        _django_center = DjangoCenterModel.sync_from_ddict(ddict)
        uuid = ddict.get("uuid")
        assert uuid is not None
        retrieved_center = DjangoCenterModel.objects.get(uuid=uuid)
        assert str(retrieved_center.uuid) == sample_center_with_examiners.uuid
        center_dict = retrieved_center.to_ddict_shallow()
        # Convert the Django model instance back to a Pydantic model
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
        self, sample_patient_with_center: Tuple[Patient, Center]
    ) -> None:
        sample_patient, sample_center = sample_patient_with_center

        DjangoCenterModel.sync_from_ddict(sample_center.to_ddict())

        ddict = sample_patient.to_ddict()
        _django_patient = DjangoPatientModel.sync_from_ddict(ddict)
        uuid = ddict.get("uuid")
        assert uuid is not None
        retrieved_patient = DjangoPatientModel.objects.get(uuid=uuid)
        assert str(retrieved_patient.uuid) == sample_patient.uuid
        patient_dict = retrieved_patient.to_ddict_shallow()
        # Convert the Django model instance back to a Pydantic model
        converted_patient = PatientShallow.model_validate(patient_dict)
        assert converted_patient.to_ddict_shallow() == sample_patient.to_ddict_shallow()

    # def test_examiner_sync(self, sample_examiner: Examiner) -> None:
    #     ddict = sample_examiner.to_ddict_shallow()
    #     _django_examiner = DjangoExaminerModel.objects.create(**ddict)
    #     uuid = ddict.get("uuid")
    #     assert uuid is not None
    #     retrieved_examiner = DjangoExaminerModel.objects.get(uuid=uuid)
    #     assert str(retrieved_examiner.uuid) == sample_examiner.uuid
    #     examiner_dict = retrieved_examiner.to_ddict_shallow()
    #     # Convert the Django model instance back to a Pydantic model
    #     converted_examiner = ExaminerShallow.model_validate(examiner_dict)
    #     assert (
    #         converted_examiner.to_ddict_shallow() == sample_examiner.to_ddict_shallow()
    #     )
