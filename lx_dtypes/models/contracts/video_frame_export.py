from __future__ import annotations

from typing import Annotated, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .json_types import JsonNull

type YamlScalar = str | int | float | bool | JsonNull
type YamlValue = YamlScalar | list[YamlValue] | dict[str, YamlValue]

PositiveInt = Annotated[int, Field(ge=1)]
VideoFrameAnnotationExportFormat: TypeAlias = Literal["csv", "json"]

_TRUE_VALUES = {"1", "true", "yes", "on"}
_FALSE_VALUES = {"0", "false", "no", "off", ""}


class VideoFrameAnnotationExportConfigPayload(BaseModel):
    """Validated YAML config for frame annotation exports."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )

    output_path: str = Field(min_length=1)
    output_dir: str | JsonNull = None
    output_format: VideoFrameAnnotationExportFormat = "csv"
    video_id: PositiveInt | JsonNull = None
    label_id: PositiveInt | JsonNull = None
    information_source_name: str | JsonNull = None
    only_true: bool | JsonNull = None
    limit: int | JsonNull = Field(default=None, ge=0)
    load_base_data: bool = False
    export_videos: bool = False
    export_frames: bool = True
    transcode_frames: bool = False
    transcode_fps: float = Field(default=50.0, gt=0.0)
    transcode_quality: int = Field(default=2, ge=1)
    transcode_ext: str = Field(default="jpg", min_length=1)
    transcode_overwrite: bool = False
    use_frame_pk_paths: bool | JsonNull = None
    use_export_flags: bool = True
    segment_ids: list[PositiveInt] | JsonNull = None
    center_key: str | JsonNull = None
    all_centers: bool = False
    only_validated: bool = True

    @field_validator(
        "only_true",
        "load_base_data",
        "export_videos",
        "export_frames",
        "transcode_frames",
        "transcode_overwrite",
        "use_frame_pk_paths",
        "use_export_flags",
        "all_centers",
        "only_validated",
        mode="before",
    )
    @classmethod
    def _coerce_payload_bool(cls, value: YamlValue) -> YamlValue:
        if value is None or isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in _TRUE_VALUES:
                return True
            if normalized in _FALSE_VALUES:
                return False
        return value

    @field_validator(
        "output_dir",
        "information_source_name",
        "center_key",
        mode="before",
    )
    @classmethod
    def _blank_to_null(cls, value: YamlValue) -> YamlValue:
        if isinstance(value, str):
            return value.strip() or None
        return value

    @field_validator("transcode_ext", mode="before")
    @classmethod
    def _normalize_frame_extension(cls, value: YamlValue) -> YamlValue:
        if isinstance(value, str):
            return value.strip().lstrip(".")
        return value


def validate_video_frame_annotation_export_config(
    payload: YamlValue,
) -> VideoFrameAnnotationExportConfigPayload:
    if not isinstance(payload, dict):
        raise ValueError("export config must be a mapping")
    return VideoFrameAnnotationExportConfigPayload.model_validate(payload)


__all__ = [
    "VideoFrameAnnotationExportConfigPayload",
    "VideoFrameAnnotationExportFormat",
    "YamlScalar",
    "YamlValue",
    "validate_video_frame_annotation_export_config",
]
