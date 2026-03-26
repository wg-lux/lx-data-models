from pathlib import Path
from typing import Any

import pytest

from lx_dtypes.utils import testing


def test_create_black_video_uses_ffmpeg_fallback(tmp_path, monkeypatch):
    ffmpeg_bin = testing.which("ffmpeg")
    if not ffmpeg_bin:
        pytest.skip("ffmpeg executable is not available")

    def raise_loader() -> tuple[Any, Any]:
        raise RuntimeError("OpenCV video writer is unavailable in this environment.")

    monkeypatch.setattr(testing, "_load_cv2_video_tools", raise_loader)

    output_path = tmp_path / "black.mp4"
    success = testing.create_black_video(output_path=output_path, duration_sec=1, fps=10)

    assert success
    assert output_path.exists()
    assert output_path.stat().st_size > 0
