"""Load immutable packaged masks and explicitly supplied host-owned masks."""

from pathlib import Path

import yaml

from lx_dtypes.models.contracts.video_masks import VideoMaskProfile

from .data_roots import package_data_root


def load_video_masks(runtime_root: Path | None = None) -> dict[str, VideoMaskProfile]:
    roots = [package_data_root() / "video_masks"]
    if runtime_root is not None:
        roots.append(runtime_root)
    profiles: dict[str, VideoMaskProfile] = {}
    for root in roots:
        for path in sorted(root.glob("*.yml")):
            profile = VideoMaskProfile.model_validate(yaml.safe_load(path.read_text()))
            if profile.name in profiles:
                raise ValueError(f"Duplicate video mask: {profile.name}")
            profiles[profile.name] = profile
    return profiles


def load_video_mask(name: str, runtime_root: Path | None = None) -> VideoMaskProfile:
    # Select by validated catalogue identity, never by a request-derived path.
    profiles = load_video_masks(runtime_root)
    try:
        return profiles[name]
    except KeyError as exc:
        raise ValueError(f"Unknown video mask: {name}") from exc
