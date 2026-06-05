from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts.patient_examination_report import (
    PatientExaminationReportMakeReportPayload,
    PatientExaminationReportSubmissionPayload,
    ReportSegmentFrameSelectionPayload,
    dump_make_report_payload,
    dump_report_submission_payload,
    validate_segment_selection_map,
)


def test_report_submission_payload_supplies_defaults() -> None:
    payload = PatientExaminationReportSubmissionPayload.model_validate(
        {
            "patient_examination_id": "7",
            "template_name": " colonoscopy ",
            "patient_data": {"dob": "1970-01-02"},
        }
    )

    assert dump_report_submission_payload(payload) == {
        "patient_examination_id": 7,
        "template_name": "colonoscopy",
        "template_version": "",
        "template_hash": "",
        "title": "",
        "status": "draft",
        "rendered_text": "",
        "editor_payload": {},
        "patient_data": {"dob": "1970-01-02"},
        "indications": [],
        "findings": [],
        "history_limit": 5,
    }


def test_make_report_payload_validates_nested_patient_identity() -> None:
    payload = PatientExaminationReportMakeReportPayload.model_validate(
        {
            "patient_examination_id": 9,
            "patient": {
                "first_name": "Ada",
                "last_name": "Lovelace",
                "dob": "1815-12-10",
            },
        }
    )

    assert dump_make_report_payload(payload) == {
        "patient_examination_id": 9,
        "patient": {
            "first_name": "Ada",
            "last_name": "Lovelace",
            "dob": date(1815, 12, 10),
        },
        "max_frames": 12,
    }


def test_segment_selection_map_normalizes_json_safe_selection_values() -> None:
    payload = validate_segment_selection_map(
        {
            "5": {
                "segment_id": "5",
                "video_id": 3,
                "frame_number": "42",
                "frame_id": 11,
                "relative_path": "frames/42.jpg",
                "updated_at": "2026-06-03T12:00:00+00:00",
                "selection_source": "set",
            },
            "ignored": "not a mapping",
        }
    )

    assert payload == {
        "5": {
            "segment_id": 5,
            "video_id": 3,
            "frame_number": 42,
            "frame_id": 11,
            "relative_path": "frames/42.jpg",
            "updated_at": "2026-06-03T12:00:00+00:00",
            "selection_source": "set",
        }
    }


def test_segment_selection_payload_rejects_invalid_ids() -> None:
    with pytest.raises(ValidationError):
        ReportSegmentFrameSelectionPayload.model_validate({"segment_id": 0})
