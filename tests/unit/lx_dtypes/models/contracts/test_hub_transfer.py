from __future__ import annotations

import pytest

from lx_dtypes.models.contracts.hub_transfer import HubTransferVideoSegmentPayload
from lx_dtypes.models.contracts.video_provenance import (
    RecordingTimeRange,
    VideoFrameTimeline,
    VideoProvenanceRecovery,
)


@pytest.mark.parametrize(
    "started,ended",
    [
        (None, None),
        ("2026-10-13T10:00:00+02:00", None),
        (None, "2026-10-13T08:01:00Z"),
        ("2026-10-13T10:00:00+02:00", "2026-10-13T08:01:00Z"),
    ],
)
def test_recording_time_range_preserves_optional_exchange_strings(
    started: str | None, ended: str | None
) -> None:
    value = RecordingTimeRange(recording_started_at=started, recording_ended_at=ended)
    assert value.model_dump(mode="json") == {
        "recording_started_at": started,
        "recording_ended_at": ended,
    }
    assert RecordingTimeRange.model_validate_json(value.model_dump_json()) == value


@pytest.mark.parametrize(
    "started,ended",
    [
        ("invalid", None),
        (None, ""),
        ("2026-10-13", None),
        (None, "2026-10-13T10:00:00"),
        ("2026-02-30T10:00:00Z", None),
        ("2026-10-13T10:00:00+02:00", "2026-10-13T08:00:00Z"),
        ("2026-10-13T10:00:00+02:00", "2026-10-13T07:59:00Z"),
    ],
)
@pytest.mark.parametrize("recovery", [False, True])
def test_recording_times_reject_invalid_input_at_shared_and_receipt_boundaries(
    started: str | None, ended: str | None, recovery: bool
) -> None:
    payload: dict[str, object] = {
        "recording_started_at": started,
        "recording_ended_at": ended,
    }
    if recovery:
        payload.update(
            recording_hash="a" * 64,
            processed_timeline=VideoFrameTimeline(
                content_hash="b" * 64,
                time_base_num=1,
                time_base_den=90000,
                presentation_timestamps=[0, 3000],
            ),
        )
    boundary = VideoProvenanceRecovery if recovery else RecordingTimeRange
    with pytest.raises(ValueError):
        boundary.model_validate(payload)


def _segment_payload() -> dict[str, object]:
    return {
        "source_node_key": "site-a",
        "source_segment_id": 42,
        "raw_video_hash": "video-hash",
        "start_frame_number": 10,
        "end_frame_number_exclusive": 20,
        "label_name": "polyp",
        "source_kind": "manual_annotation",
        "validation_state": "validated",
        "export_segment": True,
        "anonymous_provenance": {"information_source_name": "frontend"},
    }


def test_hub_transfer_segment_accepts_exclusive_frame_range() -> None:
    segment = HubTransferVideoSegmentPayload.model_validate(_segment_payload())

    assert segment.start_frame_number == 10
    assert segment.end_frame_number_exclusive == 20


def test_hub_transfer_segment_rejects_empty_frame_range() -> None:
    payload = _segment_payload()
    payload["end_frame_number_exclusive"] = 10

    with pytest.raises(ValueError, match="must exceed"):
        HubTransferVideoSegmentPayload.model_validate(payload)


def test_hub_transfer_segment_allows_model_only_for_exported_prediction() -> None:
    payload = _segment_payload()
    payload.update({"model_name": "temporal", "model_version": "1"})

    with pytest.raises(ValueError, match="exported prediction"):
        HubTransferVideoSegmentPayload.model_validate(payload)

    payload.update({"source_kind": "prediction"})
    segment = HubTransferVideoSegmentPayload.model_validate(payload)
    assert segment.model_name == "temporal"


def test_hub_transfer_segment_rejects_legacy_identity_name() -> None:
    payload = _segment_payload()
    payload["video_hash"] = payload.pop("raw_video_hash")

    with pytest.raises(ValueError, match="raw_video_hash"):
        HubTransferVideoSegmentPayload.model_validate(payload)


def test_unresolved_provenance_preserves_pts_without_claiming_frame_identity() -> None:
    from lx_dtypes.models.contracts.hub_transfer import HubTransferProvenancePayload

    timeline = VideoFrameTimeline(
        content_hash="b" * 64,
        time_base_num=1,
        time_base_den=90000,
        presentation_timestamps=[9000, 12000, 17000],
    )
    recovery = VideoProvenanceRecovery(
        recording_hash="a" * 64,
        processed_timeline=timeline,
        recording_started_at="2026-10-13T10:00:00+02:00",
        recording_ended_at="2026-10-13T10:01:00+02:00",
    )
    exchanged = HubTransferProvenancePayload.model_validate_json(
        HubTransferProvenancePayload(
            video_provenance_recovery=recovery
        ).model_dump_json()
    )
    assert exchanged.video_provenance_recovery == recovery
    assert recovery.original_timeline is None
    assert recovery.electrical_matching_eligible is False
    with pytest.raises(ValueError):
        VideoProvenanceRecovery.model_validate(
            {
                **recovery.model_dump(),
                "electrical_matching_eligible": True,
            }
        )
    with pytest.raises(ValueError):
        VideoProvenanceRecovery.model_validate(
            {
                **recovery.model_dump(),
                "source_frame_indices": [0, 1, 2],
            }
        )
