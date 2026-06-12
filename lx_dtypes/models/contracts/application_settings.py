from __future__ import annotations

from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, Field


class ApplicationSettingsBackupSourcePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    label: str = Field(min_length=1)
    path: str = Field(min_length=1)
    exists: bool
    file_count: int


class ApplicationSettingsBackupStatusPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    ready: bool
    missing_paths: Sequence[str] = Field(default_factory=tuple)
    required_path_count: int
    available_path_count: int
    source_roots: Sequence[ApplicationSettingsBackupSourcePayload] = Field(
        default_factory=tuple
    )


class ApplicationSettingsDataSetEntryPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    id: int | None = None
    value: str = ""
    label: str = ""
    dataset_type: str
    ai_model_type: str
    is_active: bool
    name_count: int


class ApplicationSettingsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    id: int | None = None
    center_id: int | None = None
    center_name: str = ""
    processor_id: int | None = None
    processor_name: str = ""
    annotator_name: str = ""
    report_template_name: str = ""
    ai_dataset_id: int | None = None
    ai_dataset_name: str = ""
    ai_dataset_type: str = ""
    center_key: str | None = None
    updated_at: str | None = None
    deployment_profile: dict[str, object]
    backup_status: ApplicationSettingsBackupStatusPayload


__all__ = [
    "ApplicationSettingsBackupSourcePayload",
    "ApplicationSettingsBackupStatusPayload",
    "ApplicationSettingsDataSetEntryPayload",
    "ApplicationSettingsPayload",
]
