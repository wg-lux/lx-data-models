from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Literal

from pydantic import ConfigDict, Field, field_validator

from lx_dtypes.models.contracts.json_types import JsonObject
from lx_dtypes.models.model import FrozenContractModel

type FrameSegmentReconciliationTrack = Literal["all", "manual", "prediction"]


class VerboseManagementCommandOptionsPayload(FrozenContractModel):
    model_config = ConfigDict(extra="ignore")

    verbose: bool


class ModelInputCommandOptionsPayload(FrozenContractModel):
    model_config = ConfigDict(extra="ignore")

    dataset_id: int = Field(gt=0)
    annotation_source_scope: str
    backbone_checkpoint: str = ""
    backbone_name: str
    epochs: int = Field(gt=0)

    @field_validator("annotation_source_scope", "backbone_name", mode="before")
    @classmethod
    def normalize_required_text(cls, value: str | float | bool | None) -> str:
        if isinstance(value, str):
            normalized = value.strip()
            if normalized:
                return normalized
        raise ValueError("command option must be a non-empty string")

    @field_validator("backbone_checkpoint", mode="before")
    @classmethod
    def normalize_backbone_checkpoint(cls, value: str | float | bool | None) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        raise ValueError("backbone_checkpoint must be a string")


class ModelTrainingResultPayload(FrozenContractModel):
    model_config = ConfigDict(extra="allow")

    model_path: str

    @field_validator("model_path", mode="before")
    @classmethod
    def normalize_model_path(cls, value: str | None) -> str:
        if isinstance(value, str) and value.strip():
            return value
        raise ValueError("model_path must be a non-empty string")


def validate_model_training_result(value: JsonObject) -> ModelTrainingResultPayload:
    return ModelTrainingResultPayload.model_validate(value)


class TrainImageMultilabelModelCommandOptionsPayload(FrozenContractModel):
    model_config = ConfigDict(extra="ignore")

    dataset_id: int = Field(gt=0)
    annotation_source_scope: str
    backbone_name: str
    backbone_checkpoint: str = ""
    epochs: int = Field(gt=0)
    batch_size: int = Field(gt=0)
    labelset_version: int = Field(gt=0)
    device: str
    freeze_backbone: bool
    treat_unlabeled_as_negative: bool

    @field_validator(
        "annotation_source_scope",
        "backbone_name",
        "device",
        mode="before",
    )
    @classmethod
    def normalize_required_text(cls, value: str | float | bool | None) -> str:
        if isinstance(value, str):
            normalized = value.strip()
            if normalized:
                return normalized
        raise ValueError("command option must be a non-empty string")

    @field_validator("backbone_checkpoint", mode="before")
    @classmethod
    def normalize_backbone_checkpoint(cls, value: str | float | bool | None) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        raise ValueError("backbone_checkpoint must be a string")


class TrainPhiRegionDetectorCommandOptionsPayload(FrozenContractModel):
    model_config = ConfigDict(extra="ignore")

    dataset_yaml: Path
    output_dir: Path
    base_model: str
    run_name: str = ""
    epochs: int = Field(gt=0)
    batch_size: int = Field(gt=0)
    input_size: int = Field(gt=0)
    device: str
    workers: int = Field(ge=0)
    patience: int = Field(ge=0)
    confidence_threshold: float = Field(ge=0.0, le=1.0)
    nms_threshold: float = Field(ge=0.0, le=1.0)
    class_ids: str = ""
    export_onnx: bool

    @field_validator("base_model", "device", mode="before")
    @classmethod
    def normalize_required_text(cls, value: str | float | bool | None) -> str:
        if isinstance(value, str):
            normalized = value.strip()
            if normalized:
                return normalized
        raise ValueError("command option must be a non-empty string")

    @field_validator("run_name", "class_ids", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: str | float | bool | None) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        raise ValueError("command option must be a string")


type TranscodeVideoQualityMode = Literal["fast", "balanced", "quality"]


class TranscodeVideoCommandOptionsPayload(FrozenContractModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    input_dir: str
    output_dir: str
    filename: str = ""
    recursive: bool
    overwrite: bool
    dry_run: bool
    allow_unmanaged_output: bool
    force_cpu: bool
    quality_mode: TranscodeVideoQualityMode
    extension: tuple[str, ...] = Field(default_factory=tuple)
    fail_on_skipped: bool
    json_output: bool = Field(validation_alias="json", serialization_alias="json")

    @field_validator("input_dir", "output_dir", mode="before")
    @classmethod
    def normalize_required_path_text(cls, value: str | Path | None) -> str:
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, str):
            normalized = value.strip()
            if normalized:
                return normalized
        raise ValueError("path command option must be a non-empty string")

    @field_validator("filename", mode="before")
    @classmethod
    def normalize_filename(cls, value: str | Path | None) -> str:
        if value is None:
            return ""
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, str):
            return value.strip()
        raise ValueError("filename must be a string")

    @field_validator("extension", mode="before")
    @classmethod
    def normalize_extensions(
        cls, value: Sequence[str] | tuple[str, ...] | list[str] | str | None
    ) -> tuple[str, ...]:
        if value is None:
            return ()
        if isinstance(value, tuple) and all(isinstance(item, str) for item in value):
            return value
        if isinstance(value, list) and all(isinstance(item, str) for item in value):
            return tuple(value)
        raise ValueError("extension must be a string sequence")


class ValidateRuntimeStorageContractCommandOptionsPayload(FrozenContractModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    json_output: bool = Field(validation_alias="json", serialization_alias="json")


class RuntimeStorageContractPayload(FrozenContractModel):
    model_config = ConfigDict(extra="ignore")

    protected_root: str
    data_root: str
    protected_paths: dict[str, str]
    public_paths: dict[str, str]
    valid: bool
    violations: list[str] = Field(default_factory=list)


type ValidateVideoFileStatus = Literal["accessible", "missing", "corrupted", "unknown"]


class ValidateVideoFilesCommandOptionsPayload(FrozenContractModel):
    model_config = ConfigDict(extra="ignore")

    video_id: int = Field(default=0, ge=0)
    verbose: bool
    fix_missing: bool = False

    @field_validator("video_id", mode="before")
    @classmethod
    def normalize_video_id(cls, value: int | str | None) -> int:
        if value is None:
            return 0
        if isinstance(value, int):
            return value
        raise ValueError("video_id must be an integer")


class ValidateVideoFileStatusPayload(FrozenContractModel):
    model_config = ConfigDict(extra="ignore")

    video_id: int = Field(ge=0)
    video_uuid: str
    status: ValidateVideoFileStatus
    path: str = ""
    size_mb: float = Field(ge=0.0)
    error: str = ""


class ReapQuarantineCommandOptionsPayload(FrozenContractModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    older_than_days: int = Field(ge=0)
    dry_run: bool
    confirm: bool
    json_output: bool = Field(validation_alias="json", serialization_alias="json")


class ReapUploadJobSourcesCommandOptionsPayload(FrozenContractModel):
    model_config = ConfigDict(extra="ignore")

    limit: int = Field(default=0, ge=0)
    repeat_until_empty: bool

    @field_validator("limit", mode="before")
    @classmethod
    def normalize_limit(cls, value: int | None) -> int:
        if value is None:
            return 0
        if isinstance(value, int):
            return value
        raise ValueError("limit must be an integer")


class ReconcileFrameSegmentAnnotationsCommandOptionsPayload(FrozenContractModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    video_ids: tuple[int, ...] = Field(default_factory=tuple)
    segment_ids: tuple[int, ...] = Field(default_factory=tuple)
    annotator: str = ""
    track: FrameSegmentReconciliationTrack
    apply_changes: bool
    json_output: bool = Field(validation_alias="json", serialization_alias="json")

    @field_validator("video_ids", "segment_ids", mode="before")
    @classmethod
    def normalize_id_tuple(
        cls, value: tuple[int, ...] | list[int] | None
    ) -> tuple[int, ...]:
        if value is None:
            return ()
        if isinstance(value, tuple) and all(isinstance(item, int) for item in value):
            return value
        if isinstance(value, list) and all(isinstance(item, int) for item in value):
            return tuple(value)
        raise ValueError("id options must be integer sequences")

    @field_validator("annotator", mode="before")
    @classmethod
    def normalize_annotator(cls, value: str | None) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        raise ValueError("annotator must be a string")


class ReconcileMediaIntegrityCommandOptionsPayload(FrozenContractModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    dry_run: bool
    json_output: bool = Field(validation_alias="json", serialization_alias="json")
    video_id: list[int] = Field(default_factory=list)
    check_frames: bool
    repair_frames: bool
    repair_frame: list[int] = Field(default_factory=list)
    check_ffmpeg_meta: bool
    repair_ffmpeg_meta: bool
    check_streamable_probe: bool
    cleanup_stale_artifacts: bool

    @field_validator("video_id", "repair_frame", mode="before")
    @classmethod
    def normalize_id_list(cls, value: list[int] | None) -> list[int]:
        if value is None:
            return []
        if isinstance(value, list) and all(isinstance(item, int) for item in value):
            return value
        raise ValueError("id options must be lists of integers")


class ReconcileSegmentValidationStateCommandOptionsPayload(FrozenContractModel):
    model_config = ConfigDict(extra="ignore")

    video_ids: list[int] = Field(default_factory=list)
    queue_cleanup: bool

    @field_validator("video_ids", mode="before")
    @classmethod
    def normalize_video_ids(cls, value: list[int] | None) -> list[int]:
        if value is None:
            return []
        if isinstance(value, list) and all(isinstance(item, int) for item in value):
            return value
        raise ValueError("video_ids must be a list of integer primary keys")


class ReconcileVideoFormatsCommandOptionsPayload(FrozenContractModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    root: list[str] = Field(default_factory=list)
    include_default_roots: bool
    no_default_roots: bool
    include_legacy_roots: bool
    extension: list[str] = Field(default_factory=list)
    dry_run: bool
    repair: bool
    in_place: bool
    allow_unmanaged_root: bool
    include_compliant: bool
    max_files: int = Field(default=0, ge=0)
    min_free_bytes: int = Field(ge=0)
    force_cpu: bool
    fail_on_non_compliant: bool
    json_output: bool = Field(validation_alias="json", serialization_alias="json")

    @field_validator("root", "extension", mode="before")
    @classmethod
    def normalize_text_list(cls, value: list[str] | None) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list) and all(isinstance(item, str) for item in value):
            return value
        raise ValueError("command option must be a list of strings")

    @field_validator("max_files", mode="before")
    @classmethod
    def normalize_max_files(cls, value: int | None) -> int:
        if value is None:
            return 0
        if isinstance(value, int):
            return value
        raise ValueError("max_files must be an integer")


class RefreshAuditLedgerIntegrityCommandOptionsPayload(FrozenContractModel):
    model_config = ConfigDict(extra="ignore")

    once: bool
    pretty: bool
    fail_on_non_verified: bool


class RegisterAiModelCommandOptionsPayload(FrozenContractModel):
    model_config = ConfigDict(extra="ignore")

    model_meta_path: str

    @field_validator("model_meta_path", mode="before")
    @classmethod
    def normalize_model_meta_path(cls, value: str | None) -> str:
        if isinstance(value, str) and value.strip():
            return value
        raise ValueError("model_meta_path must be a non-empty string")


class RegisterAiModelMetaPayload(FrozenContractModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    version: str
    model_type: str
    labelset: str
    labelset_version: int
    weights_path: str
    description: str = ""

    @field_validator(
        "name",
        "version",
        "model_type",
        "labelset",
        "weights_path",
        mode="before",
    )
    @classmethod
    def normalize_required_text(cls, value: str | float | bool | None) -> str:
        if isinstance(value, int):
            return str(value)
        if isinstance(value, str):
            normalized = value.strip()
            if normalized:
                return normalized
        raise ValueError("model metadata field must be a non-empty string")

    @field_validator("description", mode="before")
    @classmethod
    def normalize_description(cls, value: str | float | bool | None) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        raise ValueError("description must be a string")


class SetupEndoregDbCommandOptionsPayload(FrozenContractModel):
    model_config = ConfigDict(extra="ignore")

    skip_ai_setup: bool
    force_recreate: bool
    yaml_only: bool


class ShowUrlsCommandOptionsPayload(FrozenContractModel):
    model_config = ConfigDict(extra="ignore")

    format_style: str = ""

    @field_validator("format_style", mode="before")
    @classmethod
    def normalize_format_style(cls, value: str | float | bool | None) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        raise ValueError("format_style must be a string")


class ShowUrlsRoutePayload(FrozenContractModel):
    model_config = ConfigDict(extra="ignore")

    url: str = ""
    module: str = ""
    name: str = ""
    decorators: str = ""

    @field_validator("url", "module", "name", "decorators", mode="before")
    @classmethod
    def normalize_route_text(cls, value: str | float | bool | None) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        return str(value)


class ShowUrlsRoutesPayload(FrozenContractModel):
    model_config = ConfigDict(extra="ignore")

    routes: list[ShowUrlsRoutePayload]


class StorageManagementCommandOptionsPayload(FrozenContractModel):
    model_config = ConfigDict(extra="ignore")

    dry_run: bool
    force: bool
    cleanup_frames: bool
    cleanup_old_videos: bool
    cleanup_uploads: bool
    cleanup_logs: bool
    max_age_days: int = Field(ge=0)
    emergency_threshold: float = Field(ge=0.0, le=100.0)


class StorageManagementInfoPayload(FrozenContractModel):
    model_config = ConfigDict(extra="ignore")

    total_gb: float
    used_gb: float
    free_gb: float
    usage_percent: float
    project_storage_gb: float
    critical: bool
    warning: bool


class MigrateDataDirCommandOptionsPayload(FrozenContractModel):
    model_config = ConfigDict(extra="ignore")

    source_root: str
    dry_run: bool
    manifest_path: str


class MigrateMediaStorageCommandOptionsPayload(FrozenContractModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    apply: bool
    limit: int | None = None
    repeat_until_empty: bool
    json_output: bool = Field(validation_alias="json", serialization_alias="json")
    fail_fast: bool
    include_raw: bool
    include_processed: bool
    include_reports: bool
    include_streamable: bool
    delete_verified_legacy: bool
    video_ids: list[int] = Field(default_factory=list)
    hash_value: str = ""

    @field_validator("video_ids", mode="before")
    @classmethod
    def normalize_video_ids(cls, value: list[int] | None) -> list[int]:
        if value is None:
            return []
        if isinstance(value, list) and all(isinstance(item, int) for item in value):
            return value
        raise ValueError("video_ids must be a list of integer primary keys")

    @field_validator("hash_value", mode="before")
    @classmethod
    def normalize_hash_value(cls, value: str | None) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        raise ValueError("hash_value must be a string")


class MigrateVideoStreamableStorageCommandOptionsPayload(FrozenContractModel):
    model_config = ConfigDict(extra="ignore")

    video_ids: list[int] = Field(default_factory=list)
    processed_only: bool
    raw_only: bool
    dry_run: bool

    @field_validator("video_ids", mode="before")
    @classmethod
    def normalize_video_ids(cls, value: list[int] | None) -> list[int]:
        if value is None:
            return []
        if isinstance(value, list) and all(isinstance(item, int) for item in value):
            return value
        raise ValueError("video_ids must be a list of integer primary keys")


class MigrationMarkEligibleCommandOptionsPayload(FrozenContractModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    apply: bool
    limit: int = Field(default=0, ge=0)
    json_output: bool = Field(validation_alias="json", serialization_alias="json")


__all__ = [
    "FrameSegmentReconciliationTrack",
    "MigrateDataDirCommandOptionsPayload",
    "MigrateMediaStorageCommandOptionsPayload",
    "MigrateVideoStreamableStorageCommandOptionsPayload",
    "MigrationMarkEligibleCommandOptionsPayload",
    "ModelInputCommandOptionsPayload",
    "ModelTrainingResultPayload",
    "ReapQuarantineCommandOptionsPayload",
    "ReapUploadJobSourcesCommandOptionsPayload",
    "ReconcileFrameSegmentAnnotationsCommandOptionsPayload",
    "ReconcileMediaIntegrityCommandOptionsPayload",
    "ReconcileSegmentValidationStateCommandOptionsPayload",
    "ReconcileVideoFormatsCommandOptionsPayload",
    "RefreshAuditLedgerIntegrityCommandOptionsPayload",
    "RegisterAiModelCommandOptionsPayload",
    "RegisterAiModelMetaPayload",
    "RuntimeStorageContractPayload",
    "SetupEndoregDbCommandOptionsPayload",
    "ShowUrlsCommandOptionsPayload",
    "ShowUrlsRoutePayload",
    "ShowUrlsRoutesPayload",
    "StorageManagementCommandOptionsPayload",
    "StorageManagementInfoPayload",
    "TrainImageMultilabelModelCommandOptionsPayload",
    "TrainPhiRegionDetectorCommandOptionsPayload",
    "TranscodeVideoCommandOptionsPayload",
    "TranscodeVideoQualityMode",
    "ValidateRuntimeStorageContractCommandOptionsPayload",
    "ValidateVideoFileStatus",
    "ValidateVideoFileStatusPayload",
    "ValidateVideoFilesCommandOptionsPayload",
    "VerboseManagementCommandOptionsPayload",
    "validate_model_training_result",
]
