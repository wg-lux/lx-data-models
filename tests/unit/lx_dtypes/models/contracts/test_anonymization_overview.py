from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from lx_dtypes.models.contracts.anonymization_overview import (
    OverviewHlsMaterializationPayload,
    OverviewUploadJobMonitoringPayload,
)


def _now() -> datetime:
    return datetime.now(tz=UTC)


def _upload_payload() -> dict[str, object]:
    now = _now()
    return {
        "id": uuid4(),
        "status": "retrying",
        "ingest_mode": "watcher",
        "source_system": "watcher-daemon",
        "source_center_key": "center-a",
        "original_filename": "study.mp4",
        "source_file_persisted": True,
        "cleanup_status": "pending",
        "error_code": "dispatch_unavailable",
        "error_detail": "Import service is temporarily unavailable.",
        "retryable": True,
        "retry_count": 1,
        "max_retries": 3,
        "next_retry_at": now,
        "last_attempt_at": now,
        "created_at": now,
        "updated_at": now,
    }


def test_retrying_upload_job_requires_complete_retry_metadata() -> None:
    payload = OverviewUploadJobMonitoringPayload.model_validate(_upload_payload())

    assert payload.status == "retrying"
    assert payload.to_data()["retry_count"] == 1


@pytest.mark.parametrize("field", ["retryable", "next_retry_at"])
def test_terminal_upload_job_rejects_retry_metadata(field: str) -> None:
    data = _upload_payload()
    data.update(
        {
            "status": "error",
            "error_code": "processing_failed",
            "retryable": False,
            "next_retry_at": None,
        }
    )
    data[field] = True if field == "retryable" else _now()

    with pytest.raises(ValueError, match="only retrying"):
        OverviewUploadJobMonitoringPayload.model_validate(data)


def test_ready_hls_requires_materialized_segments() -> None:
    now = _now()
    with pytest.raises(ValueError, match="at least one segment"):
        OverviewHlsMaterializationPayload(
            artifact_kind="processed",
            status="ready",
            source_generation_id=uuid4(),
            target_generation_id=uuid4(),
            segment_count=0,
            created_at=now,
            updated_at=now,
        )


def test_failed_hls_requires_stable_error_code() -> None:
    now = _now()
    with pytest.raises(ValueError, match="error_code"):
        OverviewHlsMaterializationPayload(
            artifact_kind="raw",
            status="failed",
            source_generation_id=uuid4(),
            target_generation_id=uuid4(),
            segment_count=0,
            created_at=now,
            updated_at=now,
        )


def test_duplicate_import_forbids_destructive_actions() -> None:
    data = _upload_payload()
    data.update(
        {
            "status": "error",
            "error_code": "duplicate_content",
            "retryable": False,
            "next_retry_at": None,
            "allowed_actions": ["delete"],
        }
    )

    with pytest.raises(ValueError, match="allowed_actions"):
        OverviewUploadJobMonitoringPayload.model_validate(data)
