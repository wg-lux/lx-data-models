from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Literal, TypeAlias, cast

import yaml

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


@dataclass(frozen=True, slots=True)
class export_config:
    output_path: Path | str
    output_dir: Path | str | None = None
    output_format: VideoFrameAnnotationExportFormat = "csv"
    video_id: int | None = None
    label_id: int | None = None
    information_source_name: str | None = None
    only_true: bool | None = None
    limit: int | None = None
    load_base_data: bool = False
    export_videos: bool = False
    export_frames: bool = True
    transcode_frames: bool = False
    transcode_fps: float = 50.0
    transcode_quality: int = 2
    transcode_ext: str = "jpg"
    transcode_overwrite: bool = False
    use_frame_pk_paths: bool | None = None
    use_export_flags: bool = True
    segment_ids: list[int] | None = None
    center_key: str | None = None
    all_centers: bool = False
    only_validated: bool = True

    @classmethod
    def from_yaml(cls, config_path: Path | str) -> export_config:
        config_data = load_video_frame_annotation_export_config(config_path)
        return cls.from_payload(config_data)

    @classmethod
    def from_payload(
        cls,
        config_data: VideoFrameAnnotationExportConfigPayload,
    ) -> export_config:
        return cls(
            output_path=config_data.output_path,
            output_dir=config_data.output_dir,
            output_format=config_data.output_format,
            video_id=config_data.video_id,
            label_id=config_data.label_id,
            information_source_name=config_data.information_source_name,
            only_true=config_data.only_true,
            limit=config_data.limit,
            load_base_data=config_data.load_base_data,
            export_videos=config_data.export_videos,
            export_frames=config_data.export_frames,
            transcode_frames=config_data.transcode_frames,
            transcode_fps=config_data.transcode_fps,
            transcode_quality=config_data.transcode_quality,
            transcode_ext=config_data.transcode_ext,
            transcode_overwrite=config_data.transcode_overwrite,
            use_frame_pk_paths=config_data.use_frame_pk_paths,
            use_export_flags=config_data.use_export_flags,
            segment_ids=config_data.segment_ids,
            center_key=config_data.center_key,
            all_centers=config_data.all_centers,
            only_validated=config_data.only_validated,
        )


@dataclass(frozen=True, slots=True)
class export_result:
    output_path: Path
    row_count: int
    success: bool
    exported_video_count: int = 0
    exported_frame_count: int = 0
    video_output_dir: Path | None = None
    frame_output_dir: Path | None = None


def load_video_frame_annotation_export_config(
    config_path: Path | str,
) -> VideoFrameAnnotationExportConfigPayload:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"config file not found: {path}")
    loaded_config = cast(YamlValue, yaml.safe_load(path.read_text()))
    raw_config: YamlValue = {} if loaded_config is None else loaded_config
    return validate_video_frame_annotation_export_config(raw_config)


__all__ = [
    "VideoFrameAnnotationExportConfigPayload",
    "VideoFrameAnnotationExportFormat",
    "YamlScalar",
    "YamlValue",
    "export_config",
    "export_result",
    "load_video_frame_annotation_export_config",
    "validate_video_frame_annotation_export_config",
]
