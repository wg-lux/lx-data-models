from __future__ import annotations

from typing import cast

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
        "timeline_coordinates": {
            "generation": {
                "content_hash": "b" * 64,
                "time_base_num": 1,
                "time_base_den": 1000,
                "first_frame_number": 10,
                "last_frame_number": 19,
                "first_presentation_timestamp": 400,
                "last_presentation_timestamp": 760,
            },
            "recording_mapping_status": "unresolved",
        },
    }


_RECORDING_HASH = "a" * 64
_PROCESSED_HASH = "b" * 64


def _transfer_payload(
    *, provenance: dict[str, object] | None, coordinates: dict[str, object]
) -> dict[str, object]:
    segment = {
        **_segment_payload(),
        "raw_video_hash": _RECORDING_HASH,
        "start_frame_number": 1,
        "end_frame_number_exclusive": 3,
        "timeline_coordinates": coordinates,
    }
    return {
        "transfer_key": "transfer-1",
        "source_node_key": "site-a",
        "target_node_key": "hub",
        "source_center_key": "center",
        "resource_kind": "video",
        "resource_hash": _RECORDING_HASH,
        "transfer_mode": "metadata_and_processed_media",
        "processing_policy": "preserve_processing_state",
        "processing_intent": "sender_requests_state_preservation",
        "cleanup_policy": "retain_all",
        "payload_schema_version": "7.0",
        "processing_snapshot": {"sender_processing_success": True},
        "provenance": provenance,
        "resource_rows": {
            "video_file": {
                "raw_video_hash": _RECORDING_HASH,
                "processed_video_hash": _PROCESSED_HASH,
                "frame_count": 3,
            },
            "sensitive_meta": {
                "patient_uuid": "821d81f1-fb20-8e38-b777-01c67fe03001",
                "examination_uuid": "821d81f1-fb20-8e38-b777-01c67fe03002",
            },
            "video_state": {},
            "processing_history": {"file_hash": _PROCESSED_HASH, "success": True},
            "video_segments": [segment],
        },
    }


def _processed_timeline() -> dict[str, object]:
    return {
        "content_hash": _PROCESSED_HASH,
        "time_base_num": 1,
        "time_base_den": 1000,
        "presentation_timestamps": [0, 20, 40],
    }


def _verified_provenance() -> dict[str, object]:
    return {
        "video_frame_provenance": {
            "transformations": [
                {
                    "source": {
                        "content_hash": _RECORDING_HASH,
                        "time_base_num": 1,
                        "time_base_den": 90000,
                        "presentation_timestamps": [0, 3003, 6006, 9009],
                    },
                    "output": _processed_timeline(),
                    "source_frame_indices": [0, 2, 3],
                }
            ]
        }
    }


def _unresolved_provenance() -> dict[str, object]:
    return {
        "video_provenance_recovery": {
            "recording_hash": _RECORDING_HASH,
            "processed_timeline": _processed_timeline(),
        }
    }


def _coordinates(
    *, status: str = "verified", **generation: object
) -> dict[str, object]:
    coordinates: dict[str, object] = {
        "generation": {
            "content_hash": _PROCESSED_HASH,
            "time_base_num": 1,
            "time_base_den": 1000,
            "first_frame_number": 1,
            "last_frame_number": 2,
            "first_presentation_timestamp": 20,
            "last_presentation_timestamp": 40,
            **generation,
        },
        "recording_mapping_status": status,
    }
    if status == "verified":
        coordinates["recording"] = {
            "recording_content_hash": _RECORDING_HASH,
            "time_base_num": 1,
            "time_base_den": 90000,
            "first_frame_index": 2,
            "last_frame_index": 3,
            "first_presentation_timestamp": 6006,
            "last_presentation_timestamp": 9009,
        }
    return coordinates


@pytest.mark.parametrize(
    "provenance,status",
    [(_verified_provenance(), "verified"), (_unresolved_provenance(), "unresolved")],
)
def test_transfer_accepts_segment_ticks_on_processed_timeline(
    provenance: dict[str, object], status: str
) -> None:
    from lx_dtypes.models.contracts.hub_transfer import (
        HubTransferVideoTransferPayload,
    )

    payload = HubTransferVideoTransferPayload.model_validate(
        _transfer_payload(
            provenance=provenance, coordinates=_coordinates(status=status)
        )
    )

    coordinates = payload.resource_rows.video_segments[0].timeline_coordinates
    assert coordinates.recording_mapping_status == status


@pytest.mark.parametrize(
    "provenance,coordinates,message",
    [
        (None, _coordinates(), "frame provenance or an unresolved receipt"),
        (_verified_provenance(), _coordinates(status="unresolved"), "mapping_status"),
        (_unresolved_provenance(), _coordinates(), "mapping_status"),
        (
            _verified_provenance(),
            _coordinates(first_presentation_timestamp=21),
            "processed timeline",
        ),
        (
            _verified_provenance(),
            _coordinates(content_hash="c" * 64),
            "processed timeline",
        ),
        (
            _verified_provenance(),
            _coordinates(time_base_den=90000),
            "processed timeline",
        ),
    ],
)
def test_transfer_rejects_segment_ticks_without_matching_provenance(
    provenance: dict[str, object] | None,
    coordinates: dict[str, object],
    message: str,
) -> None:
    from lx_dtypes.models.contracts.hub_transfer import (
        HubTransferVideoTransferPayload,
    )

    with pytest.raises(ValueError, match=message):
        HubTransferVideoTransferPayload.model_validate(
            _transfer_payload(provenance=provenance, coordinates=coordinates)
        )


def test_transfer_rejects_recording_coordinates_of_another_recording() -> None:
    from lx_dtypes.models.contracts.hub_transfer import (
        HubTransferVideoTransferPayload,
    )

    coordinates = _coordinates()
    recording = cast(dict[str, object], coordinates["recording"])
    recording["recording_content_hash"] = "d" * 64

    with pytest.raises(ValueError, match="another recording"):
        HubTransferVideoTransferPayload.model_validate(
            _transfer_payload(
                provenance=_verified_provenance(), coordinates=coordinates
            )
        )


def test_transfer_rejects_previous_schema_version() -> None:
    from lx_dtypes.models.contracts.hub_transfer import (
        HubTransferVideoTransferPayload,
    )

    payload = _transfer_payload(
        provenance=_verified_provenance(), coordinates=_coordinates()
    )
    payload["payload_schema_version"] = "6.0"

    with pytest.raises(ValueError, match="payload_schema_version"):
        HubTransferVideoTransferPayload.model_validate(payload)


@pytest.mark.parametrize(
    "first,last", [(9, 19), (10, 20), (11, 19)], ids=["early", "terminal", "late"]
)
def test_hub_transfer_segment_coordinates_cover_included_frames(
    first: int, last: int
) -> None:
    payload = _segment_payload()
    coordinates = cast(dict[str, dict[str, object]], payload["timeline_coordinates"])
    coordinates["generation"].update(
        first_frame_number=first,
        last_frame_number=last,
        first_presentation_timestamp=first * 40,
        last_presentation_timestamp=last * 40,
    )

    with pytest.raises(ValueError, match="first and last included frame"):
        HubTransferVideoSegmentPayload.model_validate(payload)


def test_hub_transfer_segment_requires_timeline_coordinates() -> None:
    payload = _segment_payload()
    del payload["timeline_coordinates"]

    with pytest.raises(ValueError, match="timeline_coordinates"):
        HubTransferVideoSegmentPayload.model_validate(payload)


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


@pytest.mark.parametrize("as_string", [False, True])
def test_transfer_identity_preserves_uuid_roundtrip(as_string: bool) -> None:
    from uuid import UUID

    from lx_dtypes.models.contracts.hub_transfer import HubTransferSensitiveMetaPayload

    patient = UUID("821d81f1-fb20-8e38-b777-01c67fe03001")
    examination = UUID("821d81f1-fb20-8e38-b777-01c67fe03002")
    identity = HubTransferSensitiveMetaPayload.model_validate(
        {
            "patient_uuid": str(patient) if as_string else patient,
            "examination_uuid": str(examination) if as_string else examination,
        }
    )
    assert identity.patient_uuid == patient
    assert identity.examination_uuid == examination
    assert identity.model_dump(mode="json") == {
        "patient_uuid": str(patient),
        "examination_uuid": str(examination),
    }
    assert (
        HubTransferSensitiveMetaPayload.model_validate_json(identity.model_dump_json())
        == identity
    )


@pytest.mark.parametrize("invalid", [1, True, "1", "not-a-uuid", None])
@pytest.mark.parametrize("field", ["patient_uuid", "examination_uuid"])
def test_transfer_identity_rejects_invalid_uuid(field: str, invalid: object) -> None:
    from lx_dtypes.models.contracts.hub_transfer import HubTransferSensitiveMetaPayload

    payload: dict[str, object] = {
        "patient_uuid": "821d81f1-fb20-8e38-b777-01c67fe03001",
        "examination_uuid": "821d81f1-fb20-8e38-b777-01c67fe03002",
    }
    payload[field] = invalid
    with pytest.raises(ValueError):
        HubTransferSensitiveMetaPayload.model_validate(payload)


@pytest.mark.parametrize(
    "payload",
    [
        {"patient_hash": "a" * 64, "examination_hash": "b" * 64},
        {"patient_id": "1", "examination_id": 2},
        {"patient_id": True, "examination_id": 2},
        {"patient_id": 0, "examination_id": 2},
        {"patient_id": 1, "examination_id": -1},
        {"patient_id": 1, "examination_id": 2, "patient_hash": "a" * 64},
    ],
)
def test_transfer_identity_rejects_legacy_hashes_and_invalid_ids(
    payload: dict[str, object],
) -> None:
    from lx_dtypes.models.contracts.hub_transfer import HubTransferSensitiveMetaPayload

    with pytest.raises(ValueError):
        HubTransferSensitiveMetaPayload.model_validate(payload)


@pytest.mark.parametrize(
    "local_uuid",
    [
        "821d81f1-fb20-4e38-b777-01c67fe03001",  # persisted random local UUID
        "821d81f1-fb20-1e38-b777-01c67fe03001",
        "821d81f1-fb20-8e38-7777-01c67fe03001",  # version nibble without RFC variant
    ],
)
@pytest.mark.parametrize("field", ["patient_uuid", "examination_uuid"])
def test_transfer_identity_rejects_site_local_uuids(
    field: str, local_uuid: str
) -> None:
    from lx_dtypes.models.contracts.hub_transfer import HubTransferSensitiveMetaPayload

    payload: dict[str, object] = {
        "patient_uuid": "821d81f1-fb20-8e38-b777-01c67fe03001",
        "examination_uuid": "821d81f1-fb20-8e38-b777-01c67fe03002",
    }
    payload[field] = local_uuid
    with pytest.raises(ValueError, match="UUIDv8 pseudonyms"):
        HubTransferSensitiveMetaPayload.model_validate(payload)
