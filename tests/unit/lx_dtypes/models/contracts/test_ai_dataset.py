from __future__ import annotations

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts import (
    AIDataSetAttachmentResultContract,
    AIDataSetAttachVideoContract,
    AIDataSetCreateContract,
)


@pytest.mark.parametrize(
    ("dataset_type", "expected_model_type"),
    [
        ("image", "image_multilabel_classification"),
        ("video", "video_segment_classification"),
    ],
)
def test_create_contract_derives_model_type_from_dataset_type(
    dataset_type: str,
    expected_model_type: str,
) -> None:
    payload = AIDataSetCreateContract.model_validate(
        {"name": "  training cohort  ", "dataset_type": dataset_type}
    )

    assert payload.name == "training cohort"
    assert payload.ai_model_type == expected_model_type


@pytest.mark.parametrize(
    "payload",
    [
        {"name": 7, "dataset_type": "image"},
        {"name": "cohort", "dataset_type": "video", "is_active": "true"},
        {"name": "cohort", "dataset_type": "image", "description": []},
        {
            "name": "cohort",
            "dataset_type": "video",
            "ai_model_type": "image_multilabel_classification",
        },
        {"name": "cohort", "dataset_type": "image", "unknown": True},
    ],
)
def test_create_contract_rejects_coercion_mismatch_and_unknown_fields(
    payload: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        AIDataSetCreateContract.model_validate(payload)


def test_attachment_request_accepts_bulk_segment_backfill() -> None:
    request = AIDataSetAttachVideoContract.model_validate(
        {
            "include_all_annotations": True,
            "include_video_annotations": True,
            "information_source_names": ["prediction"],
        }
    )

    assert request.video_id is None
    assert request.include_frame_annotations is False
    assert request.information_source_names == ["prediction"]


@pytest.mark.parametrize(
    "payload",
    [
        {"include_all_annotations": True},
        {
            "include_all_annotations": True,
            "include_video_annotations": True,
            "video_id": 7,
        },
        {"include_video_annotations": "true"},
        {"segment_ids": ["7"]},
        {"unknown": True},
    ],
)
def test_attachment_request_rejects_ambiguous_or_coerced_payloads(
    payload: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        AIDataSetAttachVideoContract.model_validate(payload)


def test_attachment_result_accepts_null_video_for_bulk_backfill() -> None:
    result = AIDataSetAttachmentResultContract.model_validate(
        {
            "dataset_id": 3,
            "video_id": None,
            "frame_annotation_count": 0,
            "video_annotation_count": 4,
            "attached_frame_annotation_count": 0,
            "attached_segment_count": 4,
            "attached_frame_annotation_ids": [],
            "attached_segment_ids": [11, 12, 13, 14],
        }
    )

    assert result.video_id is None
    assert result.attached_segment_count == 4


@pytest.mark.parametrize(
    "payload",
    [
        {"dataset_id": "3"},
        {"dataset_id": 3, "attached_segment_count": -1},
        {"dataset_id": 3, "attached_segment_ids": [0]},
        {"dataset_id": 3, "extra": "field"},
    ],
)
def test_attachment_result_rejects_malformed_payloads(
    payload: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        AIDataSetAttachmentResultContract.model_validate(payload)
