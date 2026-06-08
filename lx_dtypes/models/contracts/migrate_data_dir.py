from __future__ import annotations

from types import NoneType
from typing import TypeAlias, TypedDict

from pydantic import BaseModel, ConfigDict, Field

MigrateDataDirNull: TypeAlias = NoneType
MigrateDataDirManifestValue: TypeAlias = str | bool | MigrateDataDirNull


class MigrateDataDirCommandOptionsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    source_root: str = Field(min_length=1)
    dry_run: bool
    manifest_path: str = ""


class MigrateDataDirManifestEntryData(TypedDict):
    source_path: str
    destination_path: str
    storage_class: str
    storage_tier: str
    retention_policy: str
    create_upload_job: bool
    reason: MigrateDataDirManifestValue
    source_sha256: MigrateDataDirManifestValue
    destination_sha256: MigrateDataDirManifestValue
    dry_run: MigrateDataDirManifestValue
    destination_exists: MigrateDataDirManifestValue
    upload_job_id: MigrateDataDirManifestValue


class MigrateDataDirManifestEntryPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    source_path: str = Field(min_length=1)
    destination_path: str = Field(min_length=1)
    storage_class: str = Field(min_length=1)
    storage_tier: str = Field(min_length=1)
    retention_policy: str = Field(min_length=1)
    create_upload_job: bool
    reason: MigrateDataDirManifestValue = None
    source_sha256: MigrateDataDirManifestValue = None
    destination_sha256: MigrateDataDirManifestValue = None
    dry_run: MigrateDataDirManifestValue = None
    destination_exists: MigrateDataDirManifestValue = None
    upload_job_id: MigrateDataDirManifestValue = None

    def to_manifest_data(self) -> MigrateDataDirManifestEntryData:
        return {
            "source_path": self.source_path,
            "destination_path": self.destination_path,
            "storage_class": self.storage_class,
            "storage_tier": self.storage_tier,
            "retention_policy": self.retention_policy,
            "create_upload_job": self.create_upload_job,
            "reason": self.reason,
            "source_sha256": self.source_sha256,
            "destination_sha256": self.destination_sha256,
            "dry_run": self.dry_run,
            "destination_exists": self.destination_exists,
            "upload_job_id": self.upload_job_id,
        }


class MigrateDataDirManifestData(TypedDict):
    command: str
    created_at: str
    source_root: str
    dry_run: bool
    migrated_entries: list[MigrateDataDirManifestEntryData]
    skipped_entries: list[MigrateDataDirManifestEntryData]


class MigrateDataDirManifestPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    command: str = Field(min_length=1)
    created_at: str = Field(min_length=1)
    source_root: str = Field(min_length=1)
    dry_run: bool
    migrated_entries: list[MigrateDataDirManifestEntryPayload] = Field(
        default_factory=list
    )
    skipped_entries: list[MigrateDataDirManifestEntryPayload] = Field(
        default_factory=list
    )

    def to_manifest_data(self) -> MigrateDataDirManifestData:
        return {
            "command": self.command,
            "created_at": self.created_at,
            "source_root": self.source_root,
            "dry_run": self.dry_run,
            "migrated_entries": [
                entry.to_manifest_data() for entry in self.migrated_entries
            ],
            "skipped_entries": [
                entry.to_manifest_data() for entry in self.skipped_entries
            ],
        }


__all__ = [
    "MigrateDataDirCommandOptionsPayload",
    "MigrateDataDirManifestData",
    "MigrateDataDirManifestEntryData",
    "MigrateDataDirManifestEntryPayload",
    "MigrateDataDirManifestPayload",
    "MigrateDataDirManifestValue",
    "MigrateDataDirNull",
]
