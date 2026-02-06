from pathlib import Path

import pytest

from lx_dtypes.models.ledger.p_video import (
    PatientVideoFile,
    # PatientVideoFileDataDict,
)
from lx_dtypes.models.ledger.p_video_segment import (
    PVideoSegment,
    PVideoSegmentDataDict,
)


@pytest.fixture
def p_video_segment_data_dict_fixture(
    patient_video_file_fixture: PatientVideoFile,
) -> PVideoSegmentDataDict:
    ddict = PVideoSegmentDataDict(
        **{
            "uuid": "123e4567-e89b-12d3-a456-426614174000",
            "start_frame_number": 100,
            "end_frame_number": 150,
            "patient_video_file": str(patient_video_file_fixture.uuid),
            "label": "test_label",  # TODO Update to actual label in KB when available
            "labelset": "test_labelset",  # TODO Update to actual labelset in KB when available
            "export_segment": True,
        }
    )
    return ddict


@pytest.fixture
def p_video_segment_fixture(
    p_video_segment_data_dict_fixture: PVideoSegmentDataDict,
) -> PVideoSegment:
    return PVideoSegment(**p_video_segment_data_dict_fixture)
