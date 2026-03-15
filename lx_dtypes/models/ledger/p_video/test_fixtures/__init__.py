from pathlib import Path

import pytest

from lx_dtypes.models.ledger.p_video import (
    PatientVideoFile,
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
) -> dict[str, object]:
    ddict: dict[str, object] = {
        **{
            "uuid": "123e4567-e89b-12d3-a456-426614174000",
            "patient": "223e4567-e89b-12d3-a456-426614174111",
            "patient_examination": "323e4567-e89b-12d3-a456-426614174222",
            "fnd": {
                "file": str(raw_video_file_path),
                "dir": None,
                "files": [],
                "dirs": [],
            },
        }
    }
    return ddict


@pytest.fixture
def patient_video_file_fixture(
    patient_video_file_data_dict_fixture: dict[str, object],
) -> PatientVideoFile:
    model = PatientVideoFile.model_validate(patient_video_file_data_dict_fixture)
    return model
