import datetime

import pytest
from pydantic import ValidationError

from lx_dtypes.models.interface.Ledger import Ledger
from lx_dtypes.models.ledger.case import Case
from lx_dtypes.models.ledger.p_examination import PExamination


def examination(patient: str = "patient-1") -> PExamination:
    return PExamination(patient=patient, examination="colonoscopy")


def test_case_groups_a_patients_examinations_transiently() -> None:
    patient_examination = examination()
    case = Case.model_validate(
        {
            "case_id": "case-42",
            "patient": "patient-1",
            "admission_date": datetime.date(2026, 7, 20),
            "leave_date": "2026-07-22T12:00:00+00:00",
            "related_examinations": [patient_examination],
        }
    )

    assert case.admission_date.tzinfo is not None
    assert case.patient_examinations == [patient_examination]
    assert case.serialized_ddict["patient_examinations"] == str(
        patient_examination.uuid
    )

    ledger = Ledger(cases={str(case.uuid): case})
    assert ledger.case_exists(str(case.uuid))
    assert "cases" not in ledger.export_record_lists()


def test_case_rejects_invalid_boundaries_and_cross_patient_examinations() -> None:
    with pytest.raises(ValidationError, match="leave_date"):
        Case.model_validate(
            {
                "case_id": "case-42",
                "patient": "patient-1",
                "admission_date": "2026-07-22T00:00:00Z",
                "leave_date": "2026-07-21T00:00:00Z",
            }
        )

    with pytest.raises(ValidationError, match="case patient"):
        Case.model_validate(
            {
                "case_id": "case-42",
                "patient": "patient-1",
                "admission_date": "2026-07-22T00:00:00Z",
                "examinations": [examination(patient="patient-2")],
            }
        )
