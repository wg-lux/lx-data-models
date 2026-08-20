from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts.media_streaming import (
    ByteRange,
    FfmpegActiveStreamThrottleState,
    FfmpegStreamThrottleState,
    MediaOperationLeaseSummary,
    dump_ffmpeg_stream_throttle_state,
    dump_media_operation_lease_summary,
)


def test_byte_range_length_and_order_validation() -> None:
    byte_range = ByteRange(start=2, end=5)

    assert byte_range.length == 4

    with pytest.raises(ValidationError):
        ByteRange(start=5, end=2)


def test_media_operation_lease_summary_dump_preserves_datetime() -> None:
    expires_at = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)

    payload = dump_media_operation_lease_summary(
        MediaOperationLeaseSummary(
            lease_type="stream",
            expires_at=expires_at,
        )
    )

    assert payload == {"lease_type": "stream", "expires_at": expires_at}


def test_ffmpeg_stream_throttle_state_dump_serializes_datetimes() -> None:
    checked_at = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)

    payload = dump_ffmpeg_stream_throttle_state(
        FfmpegActiveStreamThrottleState(
            mode="streaming",
            active_stream_leases=1,
            expired_leases=0,
            checked_at=checked_at,
            next_stream_lease_expiry=checked_at,
        )
    )

    assert payload == {
        "mode": "streaming",
        "active_stream_leases": 1,
        "expired_leases": 0,
        "checked_at": "2026-01-02T03:04:05Z",
        "next_stream_lease_expiry": "2026-01-02T03:04:05Z",
    }


def test_ffmpeg_stream_throttle_state_dump_omits_missing_expiry() -> None:
    checked_at = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)

    payload = dump_ffmpeg_stream_throttle_state(
        FfmpegStreamThrottleState(
            mode="normal",
            active_stream_leases=0,
            expired_leases=0,
            checked_at=checked_at,
        )
    )

    assert payload == {
        "mode": "normal",
        "active_stream_leases": 0,
        "expired_leases": 0,
        "checked_at": "2026-01-02T03:04:05Z",
    }
