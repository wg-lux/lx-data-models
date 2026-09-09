from __future__ import annotations

import pytest

from lx_dtypes.models.contracts.hub_transfer import HubTransferVideoSegmentPayload


def _segment_payload() -> dict[str, object]:
    return {
        "source_node_key": "site-a",
        "source_segment_id": 42,
        "video_hash": "video-hash",
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
