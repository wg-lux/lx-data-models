from __future__ import annotations

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts.video_reimport import (
    VideoReimportApiResponsePayload,
    VideoReimportDispatchResult,
    VideoReimportHistoryConfig,
    dump_video_reimport_api_response,
    dump_video_reimport_request_payload,
    validate_video_reimport_request_payload,
)


def test_video_reimport_request_payload_preserves_empty_request() -> None:
    payload = validate_video_reimport_request_payload({})

    assert dump_video_reimport_request_payload(payload) == {}


def test_video_reimport_request_payload_coerces_known_fields_and_keeps_extras() -> None:
    payload = validate_video_reimport_request_payload(
        {
            "refresh_predictions": "false",
            "model_meta_id": "4",
            "model_name": " default_model ",
            "model_meta_version": 2,
            "test_run": "yes",
            "n_test_frames": "12",
            "threshold": 0.72,
        }
    )

    assert dump_video_reimport_request_payload(payload) == {
        "refresh_predictions": False,
        "model_meta_id": 4,
        "model_name": "default_model",
        "model_meta_version": "2",
        "test_run": True,
        "n_test_frames": 12,
        "threshold": 0.72,
    }


def test_video_reimport_request_payload_rejects_invalid_positive_ids() -> None:
    with pytest.raises(ValidationError):
        validate_video_reimport_request_payload({"model_meta_id": 0})


def test_video_reimport_history_config_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        VideoReimportHistoryConfig.model_validate(
            {
                "kind": "video_reimport",
                "queue": "ffmpeg_media",
                "unexpected": "value",
            }
        )


def test_video_reimport_dispatch_result_serializes_without_none_fields() -> None:
    payload = VideoReimportDispatchResult(
        task_id="task-1",
        mode="celery",
        status="queued",
        video_id=5,
        queue="ffmpeg_media",
        history_id=8,
    )

    assert payload.to_dict() == {
        "task_id": "task-1",
        "mode": "celery",
        "status": "queued",
        "operation": "video_reimport",
        "video_id": 5,
        "queue": "ffmpeg_media",
        "history_id": 8,
    }


def test_video_reimport_dispatch_result_rejects_unknown_mode() -> None:
    with pytest.raises(ValidationError):
        VideoReimportDispatchResult.model_validate(
            {
                "task_id": "task-1",
                "mode": "thread",
                "status": "queued",
                "video_id": 5,
                "queue": "ffmpeg_media",
            }
        )


def test_video_reimport_api_response_serializes_json_payload() -> None:
    payload = VideoReimportApiResponsePayload(
        error="Video media is currently busy.",
        error_type="media_busy",
        video_id=5,
        uuid="abc",
        updated_in_place=True,
    )

    assert dump_video_reimport_api_response(payload) == {
        "error": "Video media is currently busy.",
        "error_type": "media_busy",
        "video_id": 5,
        "uuid": "abc",
        "updated_in_place": True,
    }
