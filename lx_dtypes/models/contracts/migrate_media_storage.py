from __future__ import annotations

from typing import Literal

from pydantic import Field

from lx_dtypes.models.model import FrozenContractModel

type MigrateMediaStorageNull = None
type MigrateMediaStorageLimit = int | MigrateMediaStorageNull

type MigrateMediaStorageObjectKind = Literal["report", "video"]
type MigrateMediaStorageSourceKind = Literal[
    "legacy_path",
    "streamable_path",
]
type MigrateMediaStorageRecordStatus = Literal[
    "failed",
    "migrated",
    "ok",
    "repaired",
    "streamable_synced",
    "would_migrate",
    "would_repair",
    "would_sync_streamable",
]


class MigrateMediaStorageIncludesPayload(FrozenContractModel):
    raw: bool
    processed: bool
    reports: bool
    streamable: bool


class MigrateMediaStorageRecordPayload(FrozenContractModel):
    field: str = Field(min_length=1)
    object_kind: MigrateMediaStorageObjectKind
    object_pk: str = Field(min_length=1)
    status: MigrateMediaStorageRecordStatus
    reason: str = ""
    source_kind: MigrateMediaStorageSourceKind | MigrateMediaStorageNull = None
    source_path: str = ""
    target_name: str = ""
    cleanup_eligible: bool = False
    cleanup_deleted: bool = False


class MigrateMediaStorageSummaryPayload(FrozenContractModel):
    apply: bool
    changed: int = Field(ge=0)
    cleanup_deleted: int = Field(ge=0)
    delete_verified_legacy: bool
    dry_run: bool
    failed: int = Field(ge=0)
    includes: MigrateMediaStorageIncludesPayload
    iterations: int = Field(ge=0)
    limit: MigrateMediaStorageLimit = None
    migrated: int = Field(ge=0)
    records: list[MigrateMediaStorageRecordPayload] = Field(default_factory=list)
    repaired: int = Field(ge=0)
    repeat_until_empty: bool
    scanned: int = Field(ge=0)
    selected: int = Field(ge=0)
    streamable_synced: int = Field(ge=0)
    unchanged: int = Field(ge=0)
    would_delete_legacy: int = Field(ge=0)
    would_migrate: int = Field(ge=0)
    would_repair: int = Field(ge=0)
    would_sync_streamable: int = Field(ge=0)


__all__ = [
    "MigrateMediaStorageIncludesPayload",
    "MigrateMediaStorageLimit",
    "MigrateMediaStorageNull",
    "MigrateMediaStorageObjectKind",
    "MigrateMediaStorageRecordPayload",
    "MigrateMediaStorageRecordStatus",
    "MigrateMediaStorageSourceKind",
    "MigrateMediaStorageSummaryPayload",
]
