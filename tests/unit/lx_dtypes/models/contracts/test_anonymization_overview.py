from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from lx_dtypes.models.contracts.anonymization_overview import (
    OverviewHlsMaterializationPayload,
    OverviewUploadJobMonitoringPayload,
    UploadJobCancellationResponsePayload,
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


@pytest.mark.parametrize("job_status", ["error", "lost"])
@pytest.mark.parametrize("actions", [[], ["delete"], ["safe_reimport", "delete"]])
def test_terminal_actions_can_be_restricted_by_the_endpoint(
    job_status: str, actions: list[str]
) -> None:
    data = _upload_payload()
    data.update(
        status=job_status,
        error_code="processing_failed",
        retryable=False,
        next_retry_at=None,
        allowed_actions=actions,
    )
    result = OverviewUploadJobMonitoringPayload.model_validate(data)
    assert result.to_data()["allowed_actions"] == actions


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("status", "unknown"),
        ("ingest_mode", "manual"),
        ("cleanup_status", "unknown"),
        ("error_code", "raw_exception"),
    ],
)
def test_upload_monitoring_rejects_unknown_contract_literals(
    field: str, value: str
) -> None:
    data = _upload_payload()
    data[field] = value

    with pytest.raises(ValueError):
        OverviewUploadJobMonitoringPayload.model_validate(data)


def test_hls_monitoring_rejects_unknown_error_code() -> None:
    now = _now()

    with pytest.raises(ValueError):
        OverviewHlsMaterializationPayload.model_validate(
            {
                "artifact_kind": "raw",
                "status": "failed",
                "source_generation_id": uuid4(),
                "target_generation_id": uuid4(),
                "segment_count": 0,
                "error_code": "raw_exception",
                "created_at": now,
                "updated_at": now,
            }
        )


def _cancellation_payload(status: str = "cancel_requested") -> dict[str, object]:
    data = _upload_payload()
    data.update(
        status=status,
        error_code="",
        error_detail="",
        retryable=False,
        next_retry_at=None,
        cleanup_status="skipped",
    )
    return data


@pytest.mark.parametrize("status", ["cancel_requested", "cancelled"])
def test_cancellation_response_preserves_source(status: str) -> None:
    job = OverviewUploadJobMonitoringPayload.model_validate(
        _cancellation_payload(status)
    )
    response = UploadJobCancellationResponsePayload(upload_job=job)
    assert response.to_data() == {
        "upload_job": job.to_data(),
        "cancellation_requested": True,
        "source_preserved": True,
    }
    assert (
        UploadJobCancellationResponsePayload.model_validate_json(
            response.model_dump_json()
        )
        == response
    )


@pytest.mark.parametrize("status", ["cancel_requested", "cancelled"])
@pytest.mark.parametrize("action", ["cancel", "delete", "safe_reimport"])
def test_cancellation_states_forbid_further_actions(status: str, action: str) -> None:
    data = _cancellation_payload(status)
    data["allowed_actions"] = [action]
    with pytest.raises(ValueError, match="allowed_actions"):
        OverviewUploadJobMonitoringPayload.model_validate(data)


@pytest.mark.parametrize("status", ["pending", "processing", "retrying"])
def test_active_imports_allow_cancel(status: str) -> None:
    data = _upload_payload() if status == "retrying" else _cancellation_payload(status)
    data["allowed_actions"] = ["cancel"]
    assert OverviewUploadJobMonitoringPayload.model_validate(data).allowed_actions == [
        "cancel"
    ]


@pytest.mark.parametrize("status", ["cancel_requested", "cancelled"])
@pytest.mark.parametrize("cleanup_status", ["eligible", "deleting", "completed"])
def test_cancelled_source_cannot_be_scheduled_for_cleanup(
    status: str, cleanup_status: str
) -> None:
    data = _cancellation_payload(status)
    data["cleanup_status"] = cleanup_status
    with pytest.raises(ValueError, match="cleanup"):
        OverviewUploadJobMonitoringPayload.model_validate(data)


@pytest.mark.parametrize("status", ["cancel_requested", "cancelled"])
@pytest.mark.parametrize("field", ["retryable", "next_retry_at"])
def test_cancellation_rejects_retry_scheduling(status: str, field: str) -> None:
    data = _cancellation_payload(status)
    data[field] = _upload_payload()[field]
    with pytest.raises(ValueError):
        OverviewUploadJobMonitoringPayload.model_validate(data)


@pytest.mark.parametrize("status", ["pending", "processing", "anonymized"])
def test_cancellation_response_rejects_other_states(status: str) -> None:
    job = OverviewUploadJobMonitoringPayload.model_validate(
        _cancellation_payload(status)
    )
    with pytest.raises(ValueError, match="cancellation state"):
        UploadJobCancellationResponsePayload(upload_job=job)


def test_cancellation_response_requires_persisted_source() -> None:
    data = _cancellation_payload()
    data["source_file_persisted"] = False
    job = OverviewUploadJobMonitoringPayload.model_validate(data)
    with pytest.raises(ValueError, match="preserved source"):
        UploadJobCancellationResponsePayload(upload_job=job)


@pytest.mark.parametrize("field", ["cancellation_requested", "source_preserved"])
def test_cancellation_response_rejects_false_acknowledgements(field: str) -> None:
    job = OverviewUploadJobMonitoringPayload.model_validate(_cancellation_payload())
    with pytest.raises(ValueError):
        UploadJobCancellationResponsePayload.model_validate(
            {"upload_job": job, field: False}
        )


def test_cancellation_response_forbids_unknown_fields() -> None:
    job = OverviewUploadJobMonitoringPayload.model_validate(_cancellation_payload())
    with pytest.raises(ValueError):
        UploadJobCancellationResponsePayload.model_validate(
            {"upload_job": job, "unknown": True}
        )


@pytest.mark.parametrize("status", ["cancel_requested", "cancelled"])
def test_cancellation_preserves_prior_retry_diagnostics(status: str) -> None:
    data = _upload_payload()
    data.update(
        status=status,
        retryable=False,
        next_retry_at=None,
        cleanup_status="skipped",
    )
    job = OverviewUploadJobMonitoringPayload.model_validate(data)
    response = UploadJobCancellationResponsePayload(upload_job=job).to_data()
    assert response["upload_job"]["error_code"] == "dispatch_unavailable"
    assert response["upload_job"]["error_detail"] == data["error_detail"]
    assert response["upload_job"]["retry_count"] == 1
