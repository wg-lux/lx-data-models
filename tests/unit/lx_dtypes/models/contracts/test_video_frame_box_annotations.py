from __future__ import annotations

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts.video_frame_box_annotations import (
    VideoFrameBoxAnnotationListResponsePayload,
    VideoFrameBoxAnnotationMutationResponsePayload,
    validate_video_frame_box_annotation_request,
    validate_video_phi_frame_observations,
)


def test_frame_box_request_accepts_top_level_annotation_list() -> None:
    payload = validate_video_frame_box_annotation_request(
        [
            {
                "frame_id": 3,
                "label_id": 7,
                "information_source_name": "manual_annotation",
                "x": 1,
                "y": 2,
                "width": 3,
                "height": 4,
                "image_width": 100,
                "image_height": 100,
            }
        ]
    )

    assert payload.annotations[0].frame_id == 3
    assert payload.annotations[0].label_id == 7
    assert payload.replace is False


def test_frame_box_request_normalizes_object_wrapper_aliases() -> None:
    payload = validate_video_frame_box_annotation_request(
        {
            "frame_id": "8",
            "video_id": "2",
            "replace": "true",
            "information_source": " source ",
            "annotator": " alice ",
            "annotations": [
                {
                    "label_id": 4,
                    "information_source_name": "manual_annotation",
                    "x": 1,
                    "y": 2,
                    "width": 3,
                    "height": 4,
                    "image_width": 100,
                    "image_height": 100,
                }
            ],
        }
    )

    assert payload.frame_id == 8
    assert payload.video_id == 2
    assert payload.replace is True
    assert payload.resolved_information_source_name == "source"
    assert payload.annotator == "alice"
    assert payload.annotations[0].frame_id == 8


def test_frame_box_request_forbids_unknown_wrapper_and_item_fields() -> None:
    with pytest.raises(ValidationError, match="extra_forbidden"):
        validate_video_frame_box_annotation_request(
            {"annotations": [], "unexpected": True}
        )

    with pytest.raises(ValidationError, match="extra_forbidden"):
        validate_video_frame_box_annotation_request(
            [
                {
                    "frame_id": 3,
                    "label_id": 7,
                    "information_source_name": "manual_annotation",
                    "x": 1,
                    "y": 2,
                    "width": 3,
                    "height": 4,
                    "image_width": 100,
                    "image_height": 100,
                    "unexpected": True,
                }
            ]
        )


def test_frame_box_list_response_uses_counted_annotations() -> None:
    payload = VideoFrameBoxAnnotationListResponsePayload(
        frame_id=1,
        video_id=2,
        annotations=[{"id": 3}],
        count=1,
    )

    assert payload.to_response_dict() == {
        "status": "success",
        "frame_id": 1,
        "video_id": 2,
        "annotations": [{"id": 3}],
        "count": 1,
    }


def test_frame_box_mutation_response_omits_absent_delete_count() -> None:
    payload = VideoFrameBoxAnnotationMutationResponsePayload(
        video_id=2,
        upserted_count=1,
        annotations=[{"id": 3}],
    )

    assert payload.to_response_dict() == {
        "status": "success",
        "video_id": 2,
        "upserted_count": 1,
        "annotations": [{"id": 3}],
    }


def test_phi_frame_observations_accept_missing_payload_as_empty() -> None:
    assert validate_video_phi_frame_observations(None) == []


def test_phi_frame_observations_reject_non_list_payload() -> None:
    with pytest.raises(ValueError, match="frame_observations must be a list"):
        validate_video_phi_frame_observations({"frame_number": 1})


def test_phi_frame_observations_reject_malformed_entries() -> None:
    with pytest.raises(ValidationError):
        validate_video_phi_frame_observations(
            [
                {
                    "frame_number": 1,
                    "image_width": 1280,
                    "image_height": 720,
                    "phi_regions": [{"x": 0.0, "y": 0.0, "width": -1.0, "height": 2.0}],
                }
            ]
        )
