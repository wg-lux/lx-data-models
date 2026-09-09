from pathlib import Path

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts.export_annotated import (
    ExportAnnotatedConfigContract,
)


def test_segment_scoped_pts_export_does_not_require_duplicate_filters() -> None:
    contract = ExportAnnotatedConfigContract.model_validate(
        {
            "output_dir": "data/export",
            "output_format": "json",
            "export_profile": "pts_dataset_v1",
            "video_id": 42,
            "segment_ids": [101, 102],
        }
    )

    config = contract.to_export_config()
    assert config.output_dir == Path("data/export")
    assert config.export_profile == "pts_dataset_v1"
    assert config.label_id is None
    assert config.information_source_name is None
    assert config.only_true is None
    assert config.limit is None


def test_pts_export_rejects_unknown_profile() -> None:
    with pytest.raises(ValidationError):
        ExportAnnotatedConfigContract.model_validate(
            {
                "output_dir": "data/export",
                "export_profile": "unversioned",
                "video_id": 42,
            }
        )
