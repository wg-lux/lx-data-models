from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict
from lx_dtypes.models.meta.VideoMeta import VideoRoiBox


class RoiBoxCore(VideoRoiBox):
    """
    Rectangular region of Interest in Image or Video.
    Validates positive int values and four corners specification.
    """


class EndoscopeImageRoiCore(RoiBoxCore):
    image_width: int
    image_height: int


class EndoscopyProcessorCore(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    name: str


class MaskCallPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    input_video: Path
    mask_config: RoiBoxCore
    output_video: Path
    mode: str


def roi_box_to_crop_template(
    roi: RoiBoxCore,
    *,
    image_width: int | None = None,
    image_height: int | None = None,
) -> list[int] | None:
    """
    Convert an ROI box into the crop-template shape used by video services.

    Returns [y1, y2, x1, x2]. If image dimensions are provided, the crop is
    clamped to the image boundary. Returns None if the ROI is empty or clamps
    to an empty region.
    """
    x = int(roi.x)
    y = int(roi.y)
    width = int(roi.width)
    height = int(roi.height)

    if width <= 0 or height <= 0:
        return None

    if image_width is not None and image_height is not None:
        y1 = max(0, y)
        y2 = min(int(image_height), y + height)
        x1 = max(0, x)
        x2 = min(int(image_width), x + width)
        if y1 >= y2 or x1 >= x2:
            return None
        return [y1, y2, x1, x2]

    return [y, y + height, x, x + width]


def roi_box_from_object(value: object) -> RoiBoxCore:
    """
    Normalize a VideoMeta/processor ROI-like object into RoiBoxCore.

    Accepts an existing RoiBoxCore, a mapping, or an object with x/y/width/height
    attributes.
    """
    if isinstance(value, RoiBoxCore):
        return value
    return RoiBoxCore.model_validate(value)


def roi_box_or_none_from_object(value: object | None) -> RoiBoxCore | None:
    """Normalize a nullable ROI-like object into RoiBoxCore."""
    if value is None:
        return None
    return roi_box_from_object(value)


def roi_box_to_legacy_dict(roi: RoiBoxCore) -> dict[str, int]:
    """
    Convert RoiBoxCore into the legacy dict shape still used by some helpers.

    This is intentionally centralized here so service code does not hand-roll
    dicts or index Pydantic models as mappings.
    """
    return {
        "x": int(roi.x),
        "y": int(roi.y),
        "width": int(roi.width),
        "height": int(roi.height),
    }


def all_black_fallback_roi_box() -> RoiBoxCore:
    """
    Return a valid ROI for code paths where all_black=True makes ROI irrelevant.

    RoiBoxCore validates positive dimensions, so use a minimal valid box instead
    of {} or zero-sized dicts.
    """
    return RoiBoxCore(x=0, y=0, width=1, height=1)


__all__ = [
    "RoiBoxCore",
    "EndoscopeImageRoiCore",
    "EndoscopyProcessorCore",
    "MaskCallPayload",
    "roi_box_to_legacy_dict",
    "roi_box_or_none_from_object",
    "all_black_fallback_roi_box",
    "roi_box_from_object",
    "roi_box_to_crop_template",
]
