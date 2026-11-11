from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator

from lx_dtypes.models.model import FrozenContractModel

MediaManagementCleanupType = Literal["unfinished", "failed", "stale", "all"]
MediaManagementFileType = Literal["video", "pdf", "all"]


class MediaManagementCleanupQueryPayload(FrozenContractModel):
    cleanup_type: MediaManagementCleanupType = "unfinished"
    force: bool = False
    media_type: MediaManagementFileType = "all"
    file_id: int | None = None

    @field_validator("file_id", mode="before")
    @classmethod
    def normalize_file_id(cls, value: int | str | None) -> int | None:
        if value is None or value == "":
            return None
        if isinstance(value, bool):
            raise ValueError("file_id must be an integer")  # noqa: TRY004
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            normalized = value.strip()
            if not normalized:
                return None
            return int(normalized)
        raise ValueError("file_id must be an integer")


class MediaManagementItemPayload(FrozenContractModel):
    id: int = Field(ge=1)
    type: Literal["video", "pdf"]
    filename: str | None = None
    status: str
    uploaded_at: str
    stale_duration_hours: float | None = None


class MediaManagementSummaryPayload(FrozenContractModel):
    videos_removed: int = 0
    pdfs_removed: int = 0
    total_removed: int = 0
    stale_videos_removed: int = 0
    dry_run: bool


class MediaManagementCleanupResultPayload(FrozenContractModel):
    cleanup_type: MediaManagementCleanupType
    force: bool
    removed_items: list[MediaManagementItemPayload] = Field(default_factory=list)
    summary: MediaManagementSummaryPayload = Field(
        default_factory=lambda: MediaManagementSummaryPayload(dry_run=True)
    )


class MediaManagementForceRemoveResponsePayload(FrozenContractModel):
    detail: str
    file_type: Literal["video", "pdf"]
    file_id: int


class MediaManagementResetStatusResponsePayload(FrozenContractModel):
    detail: str
    file_type: Literal["video", "pdf"]
    file_id: int


__all__ = [
    "MediaManagementCleanupQueryPayload",
    "MediaManagementCleanupResultPayload",
    "MediaManagementCleanupType",
    "MediaManagementFileType",
    "MediaManagementForceRemoveResponsePayload",
    "MediaManagementItemPayload",
    "MediaManagementResetStatusResponsePayload",
    "MediaManagementSummaryPayload",
]
