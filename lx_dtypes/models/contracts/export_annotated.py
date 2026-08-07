# endoreg_db/contracts/export_annotated.py

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Literal, Sequence, cast

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from lx_dtypes.models.contracts.video_frame_export import export_config
from lx_dtypes.models.contracts.json_types import JsonValue


def _coerce_int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float):
        if not value.is_integer():
            raise ValueError("segment ids must be integer values")
        return int(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return 0
        return int(stripped)
    raise ValueError("segment ids must be integers")


class ExportAnnotatedConfigContract(BaseModel):
    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    output_path: Path = Path("frames.csv")
    output_dir: Path
    output_format: Literal["csv", "json"] = "csv"
    export_profile: Literal["legacy_table_v1", "pts_dataset_v1"] = "pts_dataset_v1"

    video_id: int
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
    use_frame_pk_paths: bool = False

    use_export_flags: bool = True
    segment_ids: list[int] = Field(default_factory=list)

    center_key: str = ""
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
    def normalize_bool_string(
        cls, value: bool | str | int | float | None
    ) -> bool | str | int | None:
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on"}:
                return True
            if normalized in {"0", "false", "no", "off", ""}:
                return False

        if isinstance(value, float):
            if not value.is_integer():
                raise ValueError("Boolean-like number must be 0 or 1.")
            return bool(int(value))
        if isinstance(value, int):
            return bool(value)
        return value

    @field_validator("center_key", mode="before")
    @classmethod
    def normalize_center_key(cls, value: str | int | float | bool | None) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        return str(value)

    @field_validator("information_source_name", "transcode_ext", mode="before")
    @classmethod
    def normalize_required_string(
        cls, value: str | int | float | bool | None
    ) -> str | None:
        if value is None:
            return value
        if isinstance(value, str):
            return value.strip()
        return str(value).strip()

    @field_validator("output_path", "output_dir", mode="before")
    @classmethod
    def normalize_path(cls, value: Path | str | None) -> Path | str | None:
        if isinstance(value, Path):
            return value
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return value
            return Path(stripped)
        return value

    @field_validator("segment_ids", mode="before")
    @classmethod
    def normalize_segment_ids(
        cls, value: Sequence[object] | str | None
    ) -> Sequence[int] | list[int]:
        if value in (None, ""):
            return []
        if isinstance(value, str):
            parts = [part.strip() for part in value.split(",")]
            return [_coerce_int(part) for part in parts if part]
        if isinstance(value, (bytes, bytearray)):
            raise ValueError("segment_ids cannot be bytes.")
        if isinstance(value, Sequence):
            return [_coerce_int(item) for item in value]
        raise ValueError("segment_ids must be a sequence of integers.")

    @model_validator(mode="after")
    def validate_required_values(self) -> ExportAnnotatedConfigContract:
        if not self.output_dir:
            raise ValueError("output_dir is required")

        if self.video_id <= 0:
            raise ValueError("video_id must be a positive integer")

        if self.label_id is not None and self.label_id <= 0:
            raise ValueError("label_id must be a positive integer")

        if self.limit is not None and self.limit <= 0:
            raise ValueError("limit must be a positive integer")

        if not self.transcode_ext:
            raise ValueError("transcode_ext is required")

        if self.center_key and self.all_centers:
            raise ValueError(
                "Export scope must use center_key or all_centers, not both"
            )

        return self

    @property
    def resolved_output_path(self) -> Path:
        if not self.output_path.is_absolute():
            return self.output_dir / self.output_path
        return self.output_path

    @property
    def resolved_output_dir(self) -> Path:
        return self.output_dir

    @classmethod
    def from_api_payload(
        cls, payload: Mapping[str, JsonValue]
    ) -> ExportAnnotatedConfigContract:
        raw = dict(payload)

        config_path = raw.pop("config_path", None)
        if config_path:
            config_data = cls._load_yaml_payload(Path(str(config_path)))
            config_data.update(raw)
            raw = config_data

        return cls.model_validate(raw)

    @staticmethod
    def _load_yaml_payload(config_path: Path) -> dict[str, JsonValue]:
        if not config_path.exists():
            raise FileNotFoundError(f"config file not found: {config_path}")

        loaded = yaml.safe_load(config_path.read_text())

        if loaded is None:
            return {}

        if not isinstance(loaded, dict):
            raise ValueError("export config must be a mapping/object")

        return cast(dict[str, JsonValue], loaded)

    def to_export_config(self) -> export_config:
        return export_config(
            output_path=self.output_path,
            output_dir=self.output_dir,
            output_format=self.output_format,
            export_profile=self.export_profile,
            video_id=self.video_id,
            label_id=self.label_id,
            information_source_name=self.information_source_name,
            only_true=self.only_true,
            limit=self.limit,
            load_base_data=self.load_base_data,
            export_videos=self.export_videos,
            export_frames=self.export_frames,
            transcode_frames=self.transcode_frames,
            transcode_fps=self.transcode_fps,
            transcode_quality=self.transcode_quality,
            transcode_ext=self.transcode_ext,
            transcode_overwrite=self.transcode_overwrite,
            use_frame_pk_paths=self.use_frame_pk_paths,
            use_export_flags=self.use_export_flags,
            segment_ids=self.segment_ids,
            center_key=self.center_key or None,
            all_centers=self.all_centers,
            only_validated=self.only_validated,
        )
