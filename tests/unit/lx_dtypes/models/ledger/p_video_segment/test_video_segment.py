import pytest

from lx_dtypes.models.ledger.p_video_segment.Pydantic import PVideoSegment


class TestVideoSegment:
    def test_p_video_segment_creation(
        self, p_video_segment_fixture: PVideoSegment
    ) -> None:
        assert p_video_segment_fixture.start_frame_number == 100
        assert p_video_segment_fixture.end_frame_number == 150
        # assert p_video_segment_fixture.label == "Test Label"
        # assert p_video_segment_fixture.labelset == "Test Labelset"
        assert p_video_segment_fixture.export_segment is True


def _coordinates(first: int, last: int) -> dict[str, object]:
    return {
        "generation": {
            "content_hash": "b" * 64,
            "time_base_num": 1,
            "time_base_den": 1000,
            "first_frame_number": first,
            "last_frame_number": last,
            "first_presentation_timestamp": first * 40,
            "last_presentation_timestamp": last * 40,
        },
        "recording_mapping_status": "verified",
        "recording": {
            "recording_content_hash": "a" * 64,
            "time_base_num": 1,
            "time_base_den": 90000,
            "first_frame_index": first + 1,
            "last_frame_index": last + 1,
            "first_presentation_timestamp": (first + 1) * 3003,
            "last_presentation_timestamp": (last + 1) * 3003,
        },
    }


def test_p_video_segment_timeline_coordinates_survive_serialization(
    p_video_segment_fixture: PVideoSegment,
) -> None:
    segment = PVideoSegment.model_validate(
        {
            **p_video_segment_fixture.model_dump(),
            "timeline_coordinates": _coordinates(100, 149),
        }
    )

    serialized = segment.serialized_model
    assert (
        serialized.model_dump()["timeline_coordinates"]
        == (segment.model_dump()["timeline_coordinates"])
    )
    assert segment.serialized_ddict["timeline_coordinates"] is not None
    assert (
        PVideoSegment.model_validate_json(
            segment.model_dump_json()
        ).timeline_coordinates
        == segment.timeline_coordinates
    )


@pytest.mark.parametrize("first,last", [(99, 149), (100, 150), (100, 148)])
def test_p_video_segment_rejects_coordinates_for_other_frames(
    p_video_segment_fixture: PVideoSegment, first: int, last: int
) -> None:
    with pytest.raises(ValueError, match="first and last included frame"):
        PVideoSegment.model_validate(
            {
                **p_video_segment_fixture.model_dump(),
                "timeline_coordinates": _coordinates(first, last),
            }
        )
