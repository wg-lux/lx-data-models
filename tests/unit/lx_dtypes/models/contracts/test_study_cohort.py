from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts import StudyCohortCaseRow


def _grouped_case_payload() -> dict[str, object]:
    examinations = [
        {
            "patient_examination_id": 22,
            "examination_name": "follow-up",
            "examination_date": date(2026, 8, 1),
        },
        {
            "patient_examination_id": 11,
            "examination_name": "initial",
            "examination_date": date(2026, 1, 1),
        },
    ]
    return {
        "patient_examination_id": 22,
        "patient_examination_ids": [22, 11],
        "patient_id": 1,
        "examination_name": "follow-up",
        "examination_date": date(2026, 8, 1),
        "examinations": examinations,
        "center_keys": ["center-a"],
        "findings": ["re-flare-up"],
        "annotation_labels": [],
        "reports": [
            {
                "id": 7,
                "document_type": "report",
                "stream_url": "/reports/7",
                "availability": "local",
            }
        ],
        "videos": [
            {
                "id": 8,
                "stream_url": "/videos/8",
                "availability": "local",
            }
        ],
    }


def test_study_cohort_case_groups_follow_up_examinations_in_one_patient_row() -> None:
    row = StudyCohortCaseRow.model_validate(_grouped_case_payload())

    assert row.patient_id == 1
    assert row.patient_examination_ids == [22, 11]
    assert len(row.examinations) == 2
    assert [report.id for report in row.reports] == [7]
    assert [video.id for video in row.videos] == [8]


def test_study_cohort_case_rejects_inconsistent_examination_identity_lists() -> None:
    payload = _grouped_case_payload()
    payload["patient_examination_ids"] = [11, 22]

    with pytest.raises(ValidationError, match="patient_examination_ids"):
        StudyCohortCaseRow.model_validate(payload)


@pytest.mark.parametrize("field", ["patient_hash", "case_hash", "case_hashes"])
def test_study_cohort_rejects_identity_hash_fields(field: str) -> None:
    payload = _grouped_case_payload()
    payload[field] = "source-only-identity"
    with pytest.raises(ValidationError, match=field):
        StudyCohortCaseRow.model_validate(payload)
