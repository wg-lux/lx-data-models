from __future__ import annotations

from datetime import UTC, datetime

import pytest

from lx_dtypes.models.contracts import (
    ValidationError,
    VideoExaminationCreatePayload,
    VideoExaminationFindingPayload,
    VideoExaminationListQueryPayload,
    VideoExaminationUpdatePayload,
    dump_video_examination_create_payload,
    dump_video_examination_finding_payload,
    dump_video_examination_list_query_payload,
    dump_video_examination_update_payload,
    validate_video_examination_path_payload,
)


def test_video_examination_create_payload_preserves_unset_dates() -> None:
    payload = VideoExaminationCreatePayload.model_validate(
        {"video_id": 1, "examination_id": 2}
    )

    data = dump_video_examination_create_payload(payload)

    assert data == {"video_id": 1, "examination_id": 2}


def test_video_examination_update_payload_preserves_explicit_null_date() -> None:
    payload = VideoExaminationUpdatePayload.model_validate({"date_start": None})

    data = dump_video_examination_update_payload(payload)

    assert data == {"date_start": None}


def test_video_examination_payload_rejects_invalid_ids() -> None:
    with pytest.raises(ValidationError):
        VideoExaminationCreatePayload.model_validate(
            {"video_id": 0, "examination_id": 2}
        )


def test_video_examination_finding_payload_keeps_datetime_value() -> None:
    created_at = datetime(2026, 6, 3, 12, 30, tzinfo=UTC)
    payload = VideoExaminationFindingPayload(
        id=1,
        finding_id=2,
        finding_name="polyp",
        created_at=created_at,
    )

    data = dump_video_examination_finding_payload(payload)

    assert data == {
        "id": 1,
        "finding_id": 2,
        "finding_name": "polyp",
        "created_at": created_at,
    }


def test_video_examination_list_query_normalizes_blank_filters() -> None:
    payload = VideoExaminationListQueryPayload.model_validate(
        {
            "video_id": "3",
            "patient_id": "",
            "examination_id": None,
        }
    )

    data = dump_video_examination_list_query_payload(payload)

    assert data == {"video_id": 3}


def test_video_examination_path_payload_rejects_invalid_video_id() -> None:
    with pytest.raises(ValidationError):
        validate_video_examination_path_payload({"video_id": "abc"})
