from __future__ import annotations

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts.video_frame_annotations import (
    FrameAnnotationBulkEnvelopePayload,
    FrameAnnotationBulkItemPayload,
    FrameAnnotationPayloadMapping,
    FrameBoxAnnotationBulkItemPayload,
    dump_frame_annotation_bulk_item,
    dump_frame_box_annotation_bulk_item,
)


def test_frame_annotation_bulk_item_requires_label_reference() -> None:
    with pytest.raises(ValidationError):
        FrameAnnotationBulkItemPayload.model_validate(
            {
                "frame_id": 1,
                "information_source_name": "manual_annotation",
            }
        )


def test_frame_annotation_bulk_item_dump_omits_none_values() -> None:
    payload = FrameAnnotationBulkItemPayload(
        frame_id=1,
        label_id=2,
        value=False,
        information_source_name="manual_annotation",
        annotator="",
        model_meta_id=None,
    )

    assert dump_frame_annotation_bulk_item(payload) == {
        "frame_id": 1,
        "label_id": 2,
        "value": False,
        "information_source_name": "manual_annotation",
    }


def test_frame_annotation_envelope_accepts_items() -> None:
    payload = FrameAnnotationBulkEnvelopePayload.model_validate(
        {
            "video_id": "3",
            "annotations": [
                {
                    "frame_id": 1,
                    "choice_name": "polyp: present",
                    "information_source_name": "manual_annotation",
                }
            ],
        }
    )

    assert payload.video_id == 3
    assert payload.annotations[0].choice_name == "polyp: present"


def test_frame_annotation_payload_mapping_normalizes_keys() -> None:
    payload = FrameAnnotationPayloadMapping.model_validate({1: "one", "enabled": True})

    assert payload.to_json_object() == {"1": "one", "enabled": True}


def test_frame_annotation_payload_mapping_rejects_non_object() -> None:
    with pytest.raises(ValidationError):
        FrameAnnotationPayloadMapping.model_validate(["not", "an", "object"])


def test_frame_box_annotation_rejects_out_of_bounds_box() -> None:
    with pytest.raises(ValidationError):
        FrameBoxAnnotationBulkItemPayload.model_validate(
            {
                "frame_id": 1,
                "label_id": 2,
                "information_source_name": "manual_annotation",
                "x": 790,
                "y": 10,
                "width": 20,
                "height": 20,
                "image_width": 800,
                "image_height": 600,
            }
        )


def test_frame_box_annotation_dump_preserves_geometry() -> None:
    payload = FrameBoxAnnotationBulkItemPayload(
        frame_id=1,
        label_id=2,
        information_source_name="manual_annotation",
        x=10,
        y=20,
        width=30,
        height=40,
        image_width=800,
        image_height=600,
    )

    assert dump_frame_box_annotation_bulk_item(payload) == {
        "frame_id": 1,
        "label_id": 2,
        "value": True,
        "information_source_name": "manual_annotation",
        "x": 10.0,
        "y": 20.0,
        "width": 30.0,
        "height": 40.0,
        "image_width": 800,
        "image_height": 600,
    }
