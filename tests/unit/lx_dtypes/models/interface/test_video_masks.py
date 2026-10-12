from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from lx_dtypes.models.interface.video_masks import load_video_mask, load_video_masks
from lx_dtypes.models.contracts.video_masks import VideoMaskProfile


def test_packaged_default_is_available_without_runtime_directory(tmp_path: Path) -> None:
    profile = load_video_mask("olympus_cv_1500", tmp_path / "missing")
    assert profile.mask.x == 550
    assert profile.mask.width == 1350
    assert not (tmp_path / "missing").exists()


def test_explicit_runtime_root_and_duplicate_rejection(tmp_path: Path) -> None:
    profile = load_video_mask("olympus_cv_1500").model_copy(update={"name": "room_2"})
    path = tmp_path / "room.yml"
    path.write_text(yaml.safe_dump(profile.model_dump()))
    assert load_video_mask("room_2", tmp_path) == profile
    path.write_text(yaml.safe_dump(load_video_mask("olympus_cv_1500").model_dump()))
    with pytest.raises(ValueError, match="Duplicate"):
        load_video_masks(tmp_path)


@pytest.mark.parametrize("name", ["../escape", "", "/absolute", "with spaces"])
def test_profile_identity_is_portable(name: str) -> None:
    data = load_video_mask("olympus_cv_1500").model_dump()
    data["name"] = name
    with pytest.raises(ValidationError):
        VideoMaskProfile.model_validate(data)


def test_unknown_mask_never_writes_a_stub(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unknown"):
        load_video_mask("not_configured", tmp_path)
    assert list(tmp_path.iterdir()) == []
