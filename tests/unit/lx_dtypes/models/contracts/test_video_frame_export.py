from __future__ import annotations

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts import (
    VideoFrameAnnotationExportConfigPayload,
    validate_video_frame_annotation_export_config,
)
from lx_dtypes.models.contracts.video_frame_export import YamlValue


def test_video_frame_annotation_export_config_normalizes_defaults() -> None:
    payload: dict[str, YamlValue] = {
        "output_path": "frames.csv",
        "export_videos": "false",
        "export_frames": "true",
        "only_true": "yes",
        "center_key": "  ",
        "transcode_ext": ".png",
    }

    config = validate_video_frame_annotation_export_config(payload)

    assert config == VideoFrameAnnotationExportConfigPayload(
        output_path="frames.csv",
        export_videos=False,
        export_frames=True,
        only_true=True,
        center_key=None,
        transcode_ext="png",
    )
    assert config.export_profile == "legacy_table_v1"


def test_video_frame_annotation_export_config_accepts_pts_profile() -> None:
    config = validate_video_frame_annotation_export_config(
        {
            "output_path": "frames.json",
            "output_format": "json",
            "export_profile": "pts_dataset_v1",
        }
    )

    assert config.export_profile == "pts_dataset_v1"


def test_video_frame_annotation_export_config_rejects_missing_output_path() -> None:
    with pytest.raises(ValidationError):
        validate_video_frame_annotation_export_config({"export_frames": True})


def test_video_frame_annotation_export_config_rejects_non_mapping() -> None:
    with pytest.raises(ValueError, match="mapping"):
        validate_video_frame_annotation_export_config(["frames.csv"])
