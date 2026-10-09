from __future__ import annotations

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts.video_ai_labels import (
    VideoAiHuggingFaceModelPayload,
    VideoAiLabelMutationResponsePayload,
    VideoAiPredictionJobPayload,
    VideoAiPredictionModelListPayload,
    VideoAiPredictionModelMetaPayload,
    VideoAiRerunPredictionResponsePayload,
    validate_video_ai_label_name_payload,
    validate_video_ai_label_rename_payload,
    validate_video_ai_rerun_prediction_request,
)


def _model_meta_payload() -> VideoAiPredictionModelMetaPayload:
    return VideoAiPredictionModelMetaPayload(
        id=2,
        name="segmentation",
        version="1",
        description="",
        model_name="image_multilabel",
        ai_model_id=3,
        labelset_name="default_labels",
        labelset_version=1,
        labelset_id=4,
        weights_available=True,
        is_active=True,
    )


def test_rerun_prediction_request_normalizes_aliases_and_options() -> None:
    payload = validate_video_ai_rerun_prediction_request(
        {
            "huggingface_model_id": " wg-lux/model ",
            "label_set_name": " labels ",
            "replace_prediction_segments": "false",
            "delete_frames_after": "1",
            "ocr_frame_fraction": "0.25",
            "ocr_cap": "5",
            "test_run": "yes",
            "n_test_frames": "12",
            "temporal_model": "hysteresis",
        }
    )

    assert payload.resolved_huggingface_model_id == "wg-lux/model"
    assert payload.resolved_labelset_name == "labels"
    assert payload.replace_prediction_segments is False
    assert payload.delete_frames_after is True
    assert payload.ocr_frame_fraction == 0.25
    assert payload.ocr_cap == 5
    assert payload.test_run is True
    assert payload.n_test_frames == 12
    assert payload.to_temporal_options_payload()["temporal_model"] == "hysteresis"


def test_label_name_payload_rejects_blank_name() -> None:
    with pytest.raises(ValidationError):
        validate_video_ai_label_name_payload({"name": ""})


def test_label_rename_payload_rejects_missing_old_name() -> None:
    with pytest.raises(ValidationError):
        validate_video_ai_label_rename_payload({"name": "new"})


def test_label_mutation_response_omits_empty_identity_fields() -> None:
    payload = VideoAiLabelMutationResponsePayload(success="label deleted")

    assert payload.to_response_dict() == {"success": "label deleted"}


def test_prediction_model_list_payload_dump_shape() -> None:
    payload = VideoAiPredictionModelListPayload(
        models=[_model_meta_payload()],
        default_huggingface_model_id="wg-lux/model",
        default_model_name="image_multilabel",
        default_labelset_name="default_labels",
        huggingface_models=[
            VideoAiHuggingFaceModelPayload(
                model_id="wg-lux/model",
                label="Default",
                labelset_name="default_labels",
            )
        ],
    )

    data = payload.model_dump(mode="json")

    assert data["models"][0]["labelset_id"] == 4
    assert data["huggingface_models"][0]["model_id"] == "wg-lux/model"


def test_rerun_response_preserves_nullable_job_fields() -> None:
    response = VideoAiRerunPredictionResponsePayload(
        success=True,
        status="queued",
        queued=True,
        pending=False,
        video_id=1,
        model_meta=_model_meta_payload(),
        job=VideoAiPredictionJobPayload(
            task_id="task-1",
            history_id=None,
            mode="celery",
            queue="default",
        ),
        deleted_prediction_segments=None,
        prediction_segments_count=7,
    )

    data = response.to_response_dict()

    assert isinstance(data["job"], dict)
    assert data["job"]["history_id"] is None
    assert data["deleted_prediction_segments"] is None
    assert "reason" not in data
