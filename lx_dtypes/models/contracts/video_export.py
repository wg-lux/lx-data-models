from __future__ import annotations

from typing import Annotated, Literal, TypedDict, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator

PositiveInt = Annotated[int, Field(ge=1)]
type VideoAnnotationExportFormat = Literal["csv", "json"]


class VideoAnnotationExportConfigUpdateData(TypedDict, total=False):
    output_path: str
    output_dir: str
    output_format: VideoAnnotationExportFormat
    video_id: int
    label_id: int
    information_source_name: str
    only_true: bool
    limit: int
    load_base_data: bool
    export_videos: bool
    export_frames: bool
    transcode_frames: bool
    transcode_fps: float
    transcode_quality: int
    transcode_ext: str
    transcode_overwrite: bool
    use_frame_pk_paths: bool
    use_export_flags: bool
    segment_ids: list[int]
    center_key: str | None
    all_centers: bool
    only_validated: bool


class VideoAnnotationExportRequestPayload(BaseModel):
    """Validated request payload for the annotated video export endpoint."""

    model_config = ConfigDict(extra="ignore")

    config_path: str | None = None
    output_path: str | None = None
    output_dir: str | None = None
    output_format: VideoAnnotationExportFormat | None = None
    format: VideoAnnotationExportFormat | None = None
    video_id: PositiveInt | None = None
    label_id: PositiveInt | None = None
    information_source_name: str | None = None
    only_true: bool | None = None
    limit: int | None = Field(default=None, ge=0)
    load_base_data: bool | None = None
    export_videos: bool | None = None
    export_frames: bool | None = None
    transcode_frames: bool | None = None
    transcode_fps: float | None = Field(default=None, gt=0.0)
    transcode_quality: int | None = Field(default=None, ge=1)
    transcode_ext: str | None = Field(default=None, min_length=1)
    transcode_overwrite: bool | None = None
    use_frame_pk_paths: bool | None = None
    use_export_flags: bool | None = None
    segment_ids: list[PositiveInt] | None = None
    center_key: str | None = None
    all_centers: bool | None = None
    only_validated: bool | None = None

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
    def _coerce_payload_bool(
        cls, value: bool | str | int | None
    ) -> bool | str | int | None:
        if value is None or isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(value)


class VideoAnnotationExportResultPayload(BaseModel):
    """Validated success response payload for annotated video exports."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    output_path: str = Field(min_length=1)
    row_count: int = Field(ge=0)
    exported_video_count: int = Field(ge=0)
    exported_frame_count: int = Field(ge=0)
    video_output_dir: str | None = None
    frame_output_dir: str | None = None


class VideoAnnotationExportErrorPayload(BaseModel):
    """Validated error response payload for annotated video exports."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    success: Literal[False] = False
    error: str = Field(min_length=1)


def dump_video_annotation_export_update_payload(
    payload: VideoAnnotationExportRequestPayload,
) -> VideoAnnotationExportConfigUpdateData:
    data = cast(
        VideoAnnotationExportConfigUpdateData,
        payload.model_dump(
            exclude={"config_path", "format"},
            exclude_none=True,
            exclude_unset=True,
        ),
    )

    fields_set = payload.model_fields_set
    if (
        "format" in fields_set
        and payload.output_format is None
        and payload.format is not None
    ):
        data["output_format"] = payload.format
    if "center_key" in fields_set and payload.center_key is not None:
        data["center_key"] = payload.center_key.strip() or None

    return data


__all__ = [
    "VideoAnnotationExportConfigUpdateData",
    "VideoAnnotationExportErrorPayload",
    "VideoAnnotationExportFormat",
    "VideoAnnotationExportRequestPayload",
    "VideoAnnotationExportResultPayload",
    "dump_video_annotation_export_update_payload",
]
