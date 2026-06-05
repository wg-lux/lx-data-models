from __future__ import annotations

from lx_dtypes.models.contracts.video_frame_box_annotations import (
    VideoFrameBoxAnnotationListResponsePayload,
    VideoFrameBoxAnnotationMutationResponsePayload,
    validate_video_frame_box_annotation_request,
)


def test_frame_box_request_accepts_top_level_annotation_list() -> None:
    payload = validate_video_frame_box_annotation_request(
        [{"frame_id": "3", "label_id": 7}]
    )

    assert payload.annotations == [{"frame_id": "3", "label_id": 7}]
    assert payload.replace is False


def test_frame_box_request_normalizes_object_wrapper_aliases() -> None:
    payload = validate_video_frame_box_annotation_request(
        {
            "frame_id": "8",
            "video_id": "2",
            "replace": "true",
            "information_source": " source ",
            "annotator": " alice ",
            "annotations": [{"label_id": 4}],
        }
    )

    assert payload.frame_id == 8
    assert payload.video_id == 2
    assert payload.replace is True
    assert payload.resolved_information_source_name == "source"
    assert payload.annotator == "alice"


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
