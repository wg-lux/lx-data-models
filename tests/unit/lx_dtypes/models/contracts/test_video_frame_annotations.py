from __future__ import annotations

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts.video_frame_annotations import (
    FrameAnnotationBulkEnvelopePayload,
    FrameAnnotationBulkItemPayload,
    FrameAnnotationPayloadMapping,
    FrameAnnotationSkipPayload,
    FrameBoxAnnotationBulkEnvelopePayload,
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


@pytest.mark.parametrize(
    ("payload_type", "payload"),
    [
        (
            FrameAnnotationBulkItemPayload,
            {
                "frame_id": 1,
                "label_id": 2,
                "information_source_name": "manual_annotation",
                "unexpected": True,
            },
        ),
        (
            FrameAnnotationBulkEnvelopePayload,
            {"annotations": [], "unexpected": True},
        ),
        (
            FrameAnnotationSkipPayload,
            {"frame_id": 1, "unexpected": True},
        ),
    ],
)
def test_frame_annotation_mutation_payloads_forbid_unknown_fields(
    payload_type: type[FrameAnnotationBulkItemPayload]
    | type[FrameAnnotationBulkEnvelopePayload]
    | type[FrameAnnotationSkipPayload],
    payload: object,
) -> None:
    with pytest.raises(ValidationError, match="extra_forbidden"):
        payload_type.model_validate(payload)


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


def test_frame_box_envelope_fills_missing_item_frame_id() -> None:
    payload = FrameBoxAnnotationBulkEnvelopePayload.model_validate(
        {
            "frame_id": 8,
            "annotations": [
                {
                    "label_id": 2,
                    "information_source_name": "manual_annotation",
                    "x": 10,
                    "y": 20,
                    "width": 30,
                    "height": 40,
                    "image_width": 800,
                    "image_height": 600,
                }
            ],
        }
    )

    assert payload.annotations[0].frame_id == 8


@pytest.mark.parametrize(
    ("wrapper_source", "expected_source"),
    [
        ({"information_source_name": " reviewed "}, "reviewed"),
        ({"information_source": " legacy "}, "legacy"),
        ({}, "manual_annotation"),
    ],
)
def test_frame_box_envelope_inherits_or_defaults_missing_item_source(
    wrapper_source: dict[str, str],
    expected_source: str,
) -> None:
    payload = FrameBoxAnnotationBulkEnvelopePayload.model_validate(
        {
            **wrapper_source,
            "annotator": " alice ",
            "annotations": [
                {
                    "frame_id": 8,
                    "label_id": 2,
                    "x": 10,
                    "y": 20,
                    "width": 30,
                    "height": 40,
                    "image_width": 800,
                    "image_height": 600,
                }
            ],
        }
    )

    assert payload.annotations[0].information_source_name == expected_source
    assert payload.annotations[0].annotator == "alice"


def test_frame_box_envelope_preserves_explicit_item_source_and_annotator() -> None:
    payload = FrameBoxAnnotationBulkEnvelopePayload.model_validate(
        {
            "information_source_name": "wrapper_source",
            "annotator": "wrapper_annotator",
            "annotations": [
                {
                    "frame_id": 8,
                    "label_id": 2,
                    "information_source_name": "item_source",
                    "annotator": "item_annotator",
                    "x": 10,
                    "y": 20,
                    "width": 30,
                    "height": 40,
                    "image_width": 800,
                    "image_height": 600,
                }
            ],
        }
    )

    assert payload.annotations[0].information_source_name == "item_source"
    assert payload.annotations[0].annotator == "item_annotator"


def test_frame_box_envelope_rejects_conflicting_item_frame_id() -> None:
    with pytest.raises(ValidationError, match="must match"):
        FrameBoxAnnotationBulkEnvelopePayload.model_validate(
            {
                "frame_id": 8,
                "annotations": [
                    {
                        "frame_id": 9,
                        "label_id": 2,
                        "information_source_name": "manual_annotation",
                        "x": 10,
                        "y": 20,
                        "width": 30,
                        "height": 40,
                        "image_width": 800,
                        "image_height": 600,
                    }
                ],
            }
        )
