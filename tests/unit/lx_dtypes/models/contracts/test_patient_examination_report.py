from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts.patient_examination_report import (
    PatientExaminationReportMakeReportPayload,
    PatientExaminationReportSubmissionPayload,
    PreferredReportFramePayload,
    ReportSegmentFrameSelectionPayload,
    dump_make_report_payload,
    dump_report_submission_payload,
    report_json_safe_dict,
    validate_segment_selection_map,
)


def test_preferred_report_frame_preserves_zero_and_exact_timestamp() -> None:
    frame = PreferredReportFramePayload(
        video_id=7, frame_number=0, timestamp=0.04000000000000001
    )
    assert frame.model_dump() == {
        "video_id": 7,
        "frame_number": 0,
        "timestamp": 0.04000000000000001,
    }


@pytest.mark.parametrize("value", [-1, float("nan"), float("inf")])
def test_preferred_report_frame_rejects_invalid_timestamp(value: float) -> None:
    with pytest.raises(ValidationError):
        PreferredReportFramePayload(video_id=7, frame_number=0, timestamp=value)


def test_report_submission_payload_supplies_defaults() -> None:
    payload = PatientExaminationReportSubmissionPayload.model_validate(
        {
            "patient_examination_id": "7",
            "template_name": " colonoscopy ",
            "knowledge_base_module": " reporting ",
            "knowledge_base_version": " 1.2.3 ",
            "patient_data": {"dob": "1970-01-02"},
        }
    )

    assert dump_report_submission_payload(payload) == {
        "patient_examination_id": 7,
        "template_name": "colonoscopy",
        "knowledge_base_module": "reporting",
        "knowledge_base_version": "1.2.3",
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
            "knowledge_base_module": "reporting",
            "knowledge_base_version": "1.2.3",
            "patient": {
                "first_name": "Ada",
                "last_name": "Lovelace",
                "dob": "1815-12-10",
            },
        }
    )

    assert dump_make_report_payload(payload) == {
        "patient_examination_id": 9,
        "knowledge_base_module": "reporting",
        "knowledge_base_version": "1.2.3",
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
            }
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


def test_segment_selection_map_rejects_non_mapping_payload() -> None:
    with pytest.raises(ValueError):
        validate_segment_selection_map([])


def test_segment_selection_map_rejects_non_mapping_entry() -> None:
    with pytest.raises(ValueError):
        validate_segment_selection_map({"ignored": "not a mapping"})


def test_report_json_safe_dict_preserves_null_values() -> None:
    assert report_json_safe_dict({"nullable": None, "nested": {"inner": None}}) == {
        "nullable": None,
        "nested": {"inner": None},
    }


@pytest.mark.parametrize(
    "mode", ["multiple", "empty", "duplicate", "over_limit", "ambiguous"]
)
def test_report_explicit_frame_selection_contract(mode: str) -> None:
    frame = {"video_id": 7, "frame_number": 0, "timestamp": 0.0}
    frames = [frame, {**frame, "frame_number": 12, "timestamp": 0.48}]
    data: dict[str, object] = {
        "patient_examination_id": 9,
        "knowledge_base_module": "reporting",
        "knowledge_base_version": "1.2.3",
        "patient": {"first_name": "Ada", "last_name": "Lovelace", "dob": "1815-12-10"},
        "selected_frames": frames,
    }
    if mode == "empty":
        data["selected_frames"] = []
    if mode == "duplicate":
        data["selected_frames"] = [frame, frame]
    if mode == "over_limit":
        data["max_frames"] = 1
    if mode == "ambiguous":
        data["preferred_frame"] = frame
    if mode in {"multiple", "empty"}:
        dumped = dump_make_report_payload(
            PatientExaminationReportMakeReportPayload.model_validate(data)
        )
        assert "selected_frames" in dumped
        assert dumped["selected_frames"] == data["selected_frames"]
    else:
        with pytest.raises(ValidationError):
            PatientExaminationReportMakeReportPayload.model_validate(data)
