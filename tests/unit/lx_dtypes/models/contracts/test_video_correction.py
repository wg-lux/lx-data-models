from __future__ import annotations

import pytest

from lx_dtypes.models.contracts import (
    ValidationError,
    VideoCorrectionSegmentUpdatePayload,
    dump_video_correction_roi_payload,
    dump_video_correction_segment_update_payload,
    parse_video_correction_frame_ranges,
    validate_video_correction_apply_mask_payload,
    validate_video_correction_frame_removal_payload,
)


def test_apply_mask_payload_normalizes_legacy_roi_aliases() -> None:
    payload = validate_video_correction_apply_mask_payload(
        {
            "mask_type": "custom",
            "custom_mask": {
                "endoscope_x": 10,
                "endoscope_y": 20,
                "endoscope_width": 640,
                "endoscope_height": 480,
                "image_width": 1920,
                "image_height": 1080,
            },
            "use_streaming": "false",
        }
    )

    assert payload.resolved_processing_method == "direct"
    assert payload.resolved_roi is not None
    assert dump_video_correction_roi_payload(payload.resolved_roi) == {
        "x": 10.0,
        "y": 20.0,
        "width": 640.0,
        "height": 480.0,
        "image_width": 1920.0,
        "image_height": 1080.0,
    }


def test_apply_mask_payload_requires_device_name_for_device_mask() -> None:
    with pytest.raises(ValidationError):
        validate_video_correction_apply_mask_payload({"mask_type": "device"})


def test_frame_removal_payload_preserves_manual_frames_alias() -> None:
    payload = validate_video_correction_frame_removal_payload(
        {"manual_frames": [3, 1, 3], "processing_method": "streaming"}
    )

    assert payload.explicit_frames() == [3, 1, 3]
    assert payload.resolved_processing_method == "streaming"


def test_frame_removal_payload_parses_ranges() -> None:
    payload = validate_video_correction_frame_removal_payload(
        {"frame_ranges": "10-12,12,20"}
    )

    assert payload.explicit_frames() == [10, 11, 12, 20]
    assert parse_video_correction_frame_ranges("1-2,4") == [1, 2, 4]


def test_frame_removal_payload_maps_automatic_selection_alias() -> None:
    payload = validate_video_correction_frame_removal_payload(
        {"selection_method": "automatic"}
    )

    assert payload.resolved_detection_method == "automatic"


def test_segment_update_payload_dump() -> None:
    payload = VideoCorrectionSegmentUpdatePayload(
        segments_updated=1,
        segments_deleted=2,
        segments_unchanged=3,
    )

    assert dump_video_correction_segment_update_payload(payload) == {
        "segments_updated": 1,
        "segments_deleted": 2,
        "segments_unchanged": 3,
    }
