from lx_dtypes.models.ledger.p_video_segment.Pydantic import PVideoSegment


class TestVideoSegment:
    def test_p_video_segment_creation(self, p_video_segment_fixture: PVideoSegment):
        assert p_video_segment_fixture.start_frame_number == 100
        assert p_video_segment_fixture.end_frame_number == 150
        # assert p_video_segment_fixture.label == "Test Label"
        # assert p_video_segment_fixture.labelset == "Test Labelset"
        assert p_video_segment_fixture.export_segment is True
