from __future__ import annotations

import pytest

from lx_dtypes.models.contracts import (
    SegmentAnnotationInput,
    SegmentBulkValidationPayload,
    SegmentCrudPayload,
    ValidationError,
    parse_segment_annotation_input,
    validate_segment_annotation_ensure_payload,
    validate_segment_prediction_import_payload,
)


def test_segment_crud_payload_normalizes_serializer_aliases() -> None:
    payload = SegmentCrudPayload.model_validate(
        {
            "ai_dataset_id": 9,
            "video_file": 5,
            "label": 7,
            "label_name": " polyp ",
        }
    )

    assert payload.serializer_payload() == {
        "video_id": 5,
        "label_id": 7,
        "label_name": "polyp",
    }


def test_segment_annotation_input_rejects_invalid_timing() -> None:
    with pytest.raises(ValidationError):
        SegmentAnnotationInput.model_validate(
            {
                "type": "segment",
                "video_id": 1,
                "start_time": 2.0,
                "end_time": 1.0,
            }
        )


def test_parse_segment_annotation_input_returns_none_for_invalid_payload() -> None:
    assert (
        parse_segment_annotation_input(
            {
                "type": "finding",
                "video_id": 1,
                "start_time": 1.0,
                "end_time": 2.0,
            }
        )
        is None
    )


def test_bulk_validation_payload_normalizes_ids_and_defaults() -> None:
    payload = SegmentBulkValidationPayload.model_validate(
        {
            "segment_ids": 3,
            "segments": [{"id": 4, "start_time": 1.0, "end_time": 2.0}],
            "notes": None,
            "information_source_name": "",
        }
    )

    assert payload.segment_ids == [3]
    assert payload.notes == ""
    assert payload.information_source_name == "manual_annotation"
    assert list(payload.timing_by_segment_id) == [4]


def test_annotation_ensure_payload_uses_default_information_source() -> None:
    payload = validate_segment_annotation_ensure_payload(
        {"video_ids": 8},
        default_information_source_name="ai_prediction",
    )

    assert payload.video_ids == [8]
    assert payload.information_source_name == "ai_prediction"


def test_prediction_import_payload_prepares_serializer_payload() -> None:
    payload = validate_segment_prediction_import_payload(
        {
            "segments": [
                {
                    "label": " polyp ",
                    "start_time": 1.25,
                    "end_time": 2.5,
                    "export_segment": True,
                }
            ]
        }
    )

    assert payload.segments[0].serializer_payload(video_id=11) == {
        "video_id": 11,
        "label_name": "polyp",
        "start_time": 1.25,
        "end_time": 2.5,
        "export_segment": True,
    }
