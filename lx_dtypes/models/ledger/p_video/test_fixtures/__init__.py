from pathlib import Path

import pytest
from lx_dtypes.models.meta.SensitiveMeta import (
    SensitiveMetaDataDict,
    SensitiveMetaStateDataDict,
)
from lx_dtypes.models.ledger.p_video import (
    PatientVideoFile,
    PatientVideoFileDataDict,
)
from lx_dtypes.models.ledger.p_video.state import AnonymizationState
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
    sensitive_meta_state: SensitiveMetaStateDataDict = {
        "uuid": "523e4567-e89b-12d3-a456-426614174444",
        "tags": [],
        "sensitive_meta": "423e4567-e89b-12d3-a456-426614174333",
        "dob_verified": False,
        "name_verified": False,
        "examination_date_verified": False,
    }
    sensitive_meta: SensitiveMetaDataDict = {
        "uuid": "423e4567-e89b-12d3-a456-426614174333",
        "tags": [],
        "examination_date": None,
        "examination_time": None,
        "casenumber": None,
        "pseudo_patient": None,
        "pseudo_examination": None,
        "gender": "unknown",
        "pseudo_examiners": [],
        "sensitive_meta_state": sensitive_meta_state,
        "first_name": "unknown",
        "last_name": "unknown",
        "dob": None,
        "endoscope_type": None,
        "endoscope_sn": None,
        "text": None,
        "anonymized_text": None,
        "external_id": None,
    }
    ddict: PatientVideoFileDataDict = {
        "uuid": "123e4567-e89b-12d3-a456-426614174000",
        "patient": "223e4567-e89b-12d3-a456-426614174111",
        "patient_examination": "323e4567-e89b-12d3-a456-426614174222",
        "fnd": {
            "file": str(raw_video_file_path),
            "dir": str(raw_video_file_path.parent),
            "files": [],
            "dirs": [],
        },
        "anonymization_state": AnonymizationState.ANONYMIZED,
        "sensitive_meta": sensitive_meta,
        "patient_video_segments": {},
        "external_ids": {},
        "tags": [],
    }
    return ddict


@pytest.fixture
def patient_video_file_fixture(
    patient_video_file_data_dict_fixture: dict[str, object],
) -> PatientVideoFile:
    model = PatientVideoFile.model_validate(patient_video_file_data_dict_fixture)
    return model
