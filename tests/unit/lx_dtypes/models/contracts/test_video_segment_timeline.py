from __future__ import annotations

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts.video_segment_timeline import (
    VideoSegmentTimelineCoordinates,
)


def _generation(**overrides: object) -> dict[str, object]:
    return {
        "content_hash": "c" * 64,
        "time_base_num": 1,
        "time_base_den": 1000,
        "first_frame_number": 1,
        "last_frame_number": 2,
        "first_presentation_timestamp": 20,
        "last_presentation_timestamp": 40,
        **overrides,
    }


def _recording(**overrides: object) -> dict[str, object]:
    return {
        "recording_content_hash": "a" * 64,
        "time_base_num": 1,
        "time_base_den": 90000,
        "first_frame_index": 2,
        "last_frame_index": 2,
        "first_presentation_timestamp": 96006,
        "last_presentation_timestamp": 96006,
        **overrides,
    }


@pytest.mark.parametrize(
    "payload",
    [
        {
            "generation": _generation(),
            "recording_mapping_status": "verified",
            "recording": _recording(),
        },
        {
            "generation": _generation(),
            "recording_mapping_status": "verified",
            "recording": _recording(
                last_frame_index=5, last_presentation_timestamp=105015
            ),
        },
        {"generation": _generation(), "recording_mapping_status": "unresolved"},
        {
            "generation": _generation(
                last_frame_number=1, last_presentation_timestamp=20
            ),
            "recording_mapping_status": "unresolved",
        },
    ],
)
def test_valid_coordinates_round_trip_through_json(payload: dict[str, object]) -> None:
    coordinates = VideoSegmentTimelineCoordinates.model_validate(payload)

    restored = VideoSegmentTimelineCoordinates.model_validate_json(
        coordinates.model_dump_json()
    )

    assert restored == coordinates


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (
            {"generation": _generation(), "recording_mapping_status": "verified"},
            "exactly for verified ancestry",
        ),
        (
            {
                "generation": _generation(),
                "recording_mapping_status": "unresolved",
                "recording": _recording(),
            },
            "exactly for verified ancestry",
        ),
        (
            {
                "generation": _generation(last_frame_number=0),
                "recording_mapping_status": "unresolved",
            },
            "must not precede",
        ),
        (
            {
                "generation": _generation(last_presentation_timestamp=20),
                "recording_mapping_status": "unresolved",
            },
            "strictly increase",
        ),
        (
            {
                "generation": _generation(),
                "recording_mapping_status": "verified",
                "recording": _recording(first_frame_index=3),
            },
            "must not reverse",
        ),
        (
            {
                "generation": _generation(),
                "recording_mapping_status": "verified",
                "recording": _recording(last_presentation_timestamp=99009),
            },
            "strictly increase",
        ),
        (
            {
                "generation": _generation(content_hash="not-a-hash"),
                "recording_mapping_status": "unresolved",
            },
            "content_hash",
        ),
        (
            {
                "generation": _generation(),
                "recording_mapping_status": "guessed",
            },
            "recording_mapping_status",
        ),
        (
            {
                "generation": _generation(first_presentation_timestamp="20"),
                "recording_mapping_status": "unresolved",
            },
            "first_presentation_timestamp",
        ),
    ],
)
def test_invalid_coordinates_are_rejected(
    payload: dict[str, object], message: str
) -> None:
    with pytest.raises(ValidationError, match=message):
        VideoSegmentTimelineCoordinates.model_validate(payload)
