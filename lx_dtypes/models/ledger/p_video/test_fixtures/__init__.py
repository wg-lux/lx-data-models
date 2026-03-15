from pathlib import Path

import pytest

from lx_dtypes.models.ledger.p_video import (
    PatientVideoFile,
    PatientVideoFileDataDict,
)
from lx_dtypes.utils.testing import create_black_video


@pytest.fixture(scope="function")
def raw_video_file_path(tmp_path: Path) -> Path:
    video_path = tmp_path / "random_noise.mp4"
    success = create_black_video(output_path=video_path, duration_sec=5)
    assert success
    return video_path


@pytest.fixture
def patient_video_file_data_dict_fixture(
    raw_video_file_path: Path,
) -> PatientVideoFileDataDict:
    ddict = PatientVideoFileDataDict(
        **{
            "uuid": "123e4567-e89b-12d3-a456-426614174000",
            "created_at": "2024-01-01T00:00:00Z",
            "patient": "223e4567-e89b-12d3-a456-426614174111",
            "patient_examination": "323e4567-e89b-12d3-a456-426614174222",
            "fnd": {
                "file": str(raw_video_file_path),
            },
        }
    )
    return ddict


@pytest.fixture
def patient_video_file_fixture(
    patient_video_file_data_dict_fixture: dict,
) -> "PatientVideoFile":
    model = PatientVideoFile.model_validate(patient_video_file_data_dict_fixture)
    return model
