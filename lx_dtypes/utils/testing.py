from pathlib import Path
from shutil import which
from subprocess import DEVNULL, CalledProcessError, run
from typing import Any

import numpy as np

from lx_dtypes.models.knowledge_base import KB_MODELS_DJANGO
from lx_dtypes.models.ledger import L_MODELS_DJANGO


def _load_cv2_video_tools() -> tuple[Any, Any]:
    try:
        from cv2 import VideoWriter, VideoWriter_fourcc
    except ImportError as exc:
        raise RuntimeError(
            "OpenCV video writer is unavailable in this environment."
        ) from exc
    return VideoWriter, VideoWriter_fourcc


def validate_django_fixture(
    model_fixture: KB_MODELS_DJANGO | L_MODELS_DJANGO,
) -> None:
    _ddict = model_fixture.ddict
    assert _ddict["uuid"] == model_fixture.uuid

    list_type_fields = model_fixture.list_type_fields()
    m2m_fields = model_fixture.m2m_fields()
    for field in list_type_fields:
        if field in m2m_fields:
            continue  # skip m2m fields here
        value = getattr(model_fixture, field)
        assert isinstance(value, str)

        value_from_ddict = _ddict.get(field, [])
        assert isinstance(value_from_ddict, list)

    for field in m2m_fields:
        value = getattr(model_fixture, field)
        assert hasattr(value, "all")  # m2m fields should have an 'all' method

        value_from_ddict = _ddict.get(field, [])
        assert isinstance(value_from_ddict, list)


def create_random_noise_video(
    output_path: Path,
    duration_sec: int = 5,
    fps: int = 50,
    width: int = 1920,
    height: int = 1080,
    fourcc_str: str = "mp4v",
    overwrite: bool = True,
) -> bool:
    VideoWriter, VideoWriter_fourcc = _load_cv2_video_tools()

    if output_path.exists() and not overwrite:
        return False
    elif output_path.exists() and overwrite:
        output_path.unlink()

    if len(fourcc_str) != 4:
        raise ValueError("fourcc_str must be exactly 4 characters long.")

    try:
        fourcc = VideoWriter_fourcc(*fourcc_str)  # type: ignore
    except Exception as e:
        raise RuntimeError(
            f"Failed to create fourcc for {fourcc_str} codec. Ensure OpenCV is properly installed."
        ) from e

    n_frames = duration_sec * fps
    try:
        out = VideoWriter(str(output_path), fourcc, fps, (width, height))

        for _ in range(n_frames):
            frame = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
            out.write(frame)

        out.release()
        return True
    except Exception as e:
        # cleanup
        if output_path.exists():
            output_path.unlink()
        raise RuntimeError(
            f"Failed to create random noise video at {output_path}."
        ) from e


def _create_black_video_with_cv2(
    output_path: Path,
    duration_sec: int,
    fps: int,
    width: int,
    height: int,
    fourcc_str: str,
    overwrite: bool,
) -> bool:
    VideoWriter, VideoWriter_fourcc = _load_cv2_video_tools()

    if output_path.exists() and not overwrite:
        return False
    elif output_path.exists() and overwrite:
        output_path.unlink()

    if len(fourcc_str) != 4:
        raise ValueError("fourcc_str must be exactly 4 characters long.")

    try:
        fourcc = VideoWriter_fourcc(*fourcc_str)  # type: ignore
    except Exception as e:
        raise RuntimeError(
            f"Failed to create fourcc for {fourcc_str} codec. Ensure OpenCV is properly installed."
        ) from e

    n_frames = duration_sec * fps

    try:
        out = VideoWriter(str(output_path), fourcc, fps, (width, height))

        black_frame = np.zeros((height, width, 3), dtype=np.uint8)
        for _ in range(n_frames):
            out.write(black_frame)

        out.release()
        return True
    except Exception as e:
        # cleanup
        if output_path.exists():
            output_path.unlink()
        raise RuntimeError(f"Failed to create black video at {output_path}.") from e


def _create_black_video_with_ffmpeg(
    output_path: Path,
    duration_sec: int,
    fps: int,
    width: int,
    height: int,
    overwrite: bool,
) -> bool:
    if output_path.exists() and not overwrite:
        return False
    if output_path.exists():
        output_path.unlink()

    ffmpeg_path = which("ffmpeg")
    if not ffmpeg_path:
        raise RuntimeError("ffmpeg is required to create a fallback black video.")

    color_size = f"{width}x{height}"
    cmd = [
        ffmpeg_path,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c=black:s={color_size}:r={fps}",
        "-t",
        str(duration_sec),
        "-pix_fmt",
        "yuv420p",
        str(output_path),
    ]

    try:
        run(cmd, check=True, stdout=DEVNULL, stderr=DEVNULL)
        return True
    except CalledProcessError as exc:
        if output_path.exists():
            output_path.unlink()
        raise RuntimeError(
            f"ffmpeg failed to produce black video at {output_path}."
        ) from exc


def create_black_video(
    output_path: Path,
    duration_sec: int = 5,
    fps: int = 50,
    width: int = 1920,
    height: int = 1080,
    fourcc_str: str = "mp4v",
    overwrite: bool = True,
) -> bool:
    try:
        return _create_black_video_with_cv2(
            output_path,
            duration_sec,
            fps,
            width,
            height,
            fourcc_str,
            overwrite,
        )
    except RuntimeError as exc:
        if "OpenCV video writer is unavailable" in str(exc):
            return _create_black_video_with_ffmpeg(
                output_path,
                duration_sec,
                fps,
                width,
                height,
                overwrite,
            )
        raise
