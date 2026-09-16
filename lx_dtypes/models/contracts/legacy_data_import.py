from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel, ConfigDict, Field

type NullValue = None
type LegacyExaminationIdValue = str | int | NullValue
type LegacyTextOrNull = str | NullValue
type LegacyIntOrNull = int | NullValue


class LegacyDataImportCommandOptionsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    jsonl_path: str = Field(min_length=1)
    images_root: str = Field(min_length=1)
    video_id: LegacyIntOrNull = None
    center_id: LegacyIntOrNull = None
    dataset_name: str = Field(min_length=1)
    dataset_description: str = Field(min_length=1)
    labelset_name: str = Field(min_length=1)
    labelset_version: int = Field(ge=1)
    dry_run: bool
    staged_images_root: str = ""
    manifest_path: str = ""


class LegacyImageImportRowPayload(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True, strict=True)

    filename: str = Field(min_length=1)
    labels: list[str] = Field(default_factory=list)
    old_examination_id: LegacyExaminationIdValue = None

    def normalized_old_examination_id(self) -> LegacyTextOrNull:
        if self.old_examination_id is None:
            return None
        normalized = str(self.old_examination_id).strip()
        return normalized or None


class LegacyImportManifestData(TypedDict):
    command: str
    created_at: str
    jsonl_path: str
    images_root: str
    staged_images_root: str
    fallback_video_id: LegacyIntOrNull
    center_id: int
    used_video_ids: list[int]
    legacy_video_ids_by_old_examination_id: dict[str, LegacyIntOrNull]
    dataset_name: str
    frame_count: int
    annotation_count: int
    copied_image_count: int
    missing_image_count: int


class LegacyImportManifestPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    command: str = Field(min_length=1)
    created_at: str = Field(min_length=1)
    jsonl_path: str = Field(min_length=1)
    images_root: str = Field(min_length=1)
    staged_images_root: str = Field(min_length=1)
    fallback_video_id: LegacyIntOrNull = None
    center_id: int
    used_video_ids: list[int]
    legacy_video_ids_by_old_examination_id: dict[str, LegacyIntOrNull]
    dataset_name: str = Field(min_length=1)
    frame_count: int = Field(ge=0)
    annotation_count: int = Field(ge=0)
    copied_image_count: int = Field(ge=0)
    missing_image_count: int = Field(ge=0)


def dump_legacy_import_manifest(
    payload: LegacyImportManifestPayload,
) -> LegacyImportManifestData:
    return {
        "command": payload.command,
        "created_at": payload.created_at,
        "jsonl_path": payload.jsonl_path,
        "images_root": payload.images_root,
        "staged_images_root": payload.staged_images_root,
        "fallback_video_id": payload.fallback_video_id,
        "center_id": payload.center_id,
        "used_video_ids": payload.used_video_ids,
        "legacy_video_ids_by_old_examination_id": (
            payload.legacy_video_ids_by_old_examination_id
        ),
        "dataset_name": payload.dataset_name,
        "frame_count": payload.frame_count,
        "annotation_count": payload.annotation_count,
        "copied_image_count": payload.copied_image_count,
        "missing_image_count": payload.missing_image_count,
    }


__all__ = [
    "LegacyDataImportCommandOptionsPayload",
    "LegacyExaminationIdValue",
    "LegacyImageImportRowPayload",
    "LegacyImportManifestData",
    "LegacyImportManifestPayload",
    "LegacyIntOrNull",
    "LegacyTextOrNull",
    "NullValue",
    "dump_legacy_import_manifest",
]
