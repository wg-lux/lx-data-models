# endoreg_db/contracts/ai_dataset.py

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Literal, cast
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from lx_dtypes.models.contracts.json_types import JsonObject


class AIDataSetScoredActiveLearningCandidateContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sample_index: int
    video_id: int
    frame_number: int
    frame_id: int
    timestamp: float
    segment_id: int
    probs: list[float]
    quality_score: float
    uncertainty: float
    diversity: float
    rarity: float
    quality_gate: float
    frame_score: float


DatasetType = Literal["image", "video"]
AIModelType = Literal[
    "image_multilabel_classification",
    "phi_region_detector",
    "video_segment_classification",
]
TrainingRunStatus = Literal["queued", "running", "completed", "failed", "lost"]
ExportArtifactStatus = Literal["running", "completed", "failed"]


def _empty_selected_sample_indices() -> list[int]:
    return []


def _empty_selected_frame_ids() -> list[int]:
    return []


def _empty_selected_candidates() -> list[
    AIDataSetScoredActiveLearningCandidateContract
]:
    return []


class AIDataSetActiveLearningConfigContractContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    budget: int = 32
    segment_gap_frames: int = 150
    temporal_spacing_frames: int = 75
    min_quality_score: float = 0.35
    max_samples_per_segment: int = 1
    max_rarity_boost: float = 2.0
    max_label_weight: float = 3.0

    @field_validator(
        "budget",
        "segment_gap_frames",
        "temporal_spacing_frames",
        "max_samples_per_segment",
    )
    @classmethod
    def positive_int(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("value must be positive")
        return value

    @field_validator("min_quality_score")
    @classmethod
    def quality_score_range(cls, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            raise ValueError("min_quality_score must be between 0 and 1")
        return value

    @field_validator("max_rarity_boost", "max_label_weight")
    @classmethod
    def positive_float(cls, value: float) -> float:
        if value <= 0.0:
            raise ValueError("value must be positive")
        return value


class AIDataSetActiveLearningCandidateContractContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sample_index: int
    video_id: int
    frame_number: int
    frame_id: int
    timestamp: float
    probs: list[float]
    embedding: list[float]
    quality_score: float

    @field_validator("probs", "embedding")
    @classmethod
    def non_empty_float_vector(cls, value: list[float]) -> list[float]:
        if not value:
            raise ValueError("vector must not be empty")
        return value

    @field_validator("quality_score")
    @classmethod
    def optional_quality_score_range(cls, value: float | None) -> float | None:
        if value is None:
            return None
        if not 0.0 <= value <= 1.0:
            raise ValueError("quality_score must be between 0 and 1")
        return value


class AIDataSetScoredActiveLearningCandidateContractContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sample_index: int
    video_id: int
    frame_number: int
    frame_id: int
    timestamp: float
    segment_id: int
    probs: list[float]
    quality_score: float
    uncertainty: float
    diversity: float
    rarity: float
    quality_gate: float
    frame_score: float


class AIDataSetActiveLearningSelectionContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    config: AIDataSetActiveLearningConfigContractContract
    candidate_count: int
    segment_count: int
    selected_sample_indices: list[int] = Field(
        default_factory=_empty_selected_sample_indices,
    )
    selected_frame_ids: list[int] = Field(default_factory=_empty_selected_frame_ids)
    selected_candidates: list[AIDataSetScoredActiveLearningCandidateContract] = Field(
        default_factory=_empty_selected_candidates,
    )


class AIDataSetContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    name: str
    description: str
    ai_model_type: AIModelType = "image_multilabel_classification"
    dataset_type: DatasetType = "image"
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    image_annotation_count: int = 0
    video_annotation_count: int = 0

    @field_validator("name", "description", mode="before")
    @classmethod
    def blank_string_to_none(cls, value: str | float | bool | None) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or ""
        return str(value)

    @model_validator(mode="after")
    def validate_model_type_matches_dataset_type(self) -> AIDataSetContract:
        allowed_by_dataset_type: dict[str, set[AIModelType]] = {
            "image": {"image_multilabel_classification", "phi_region_detector"},
            "video": {"video_segment_classification"},
        }
        allowed = allowed_by_dataset_type[self.dataset_type]
        if self.ai_model_type not in allowed:
            raise ValueError(
                f"ai_model_type={self.ai_model_type!r} is not compatible with "
                f"dataset_type={self.dataset_type!r}; expected one of {sorted(allowed)!r}."
            )
        return self


class AIDataSetCreateContract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    name: str
    description: str = ""
    dataset_type: DatasetType = "image"
    ai_model_type: AIModelType
    is_active: bool = True

    @model_validator(mode="before")
    @classmethod
    def fill_default_ai_model_type(cls, value: object) -> object:
        if not isinstance(value, Mapping):
            return value
        candidate = dict(cast(Mapping[object, object], value))
        dataset_type = candidate.get("dataset_type", "image")
        expected_by_dataset_type: dict[object, AIModelType] = {
            "image": "image_multilabel_classification",
            "video": "video_segment_classification",
        }
        if candidate.get("ai_model_type") in (None, ""):
            expected = (
                expected_by_dataset_type.get(dataset_type)
                if isinstance(dataset_type, str)
                else None
            )
            if expected is not None:
                candidate["ai_model_type"] = expected
        return candidate

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("name is required")
        if len(normalized) > 255:
            raise ValueError("name must be 255 characters or fewer")
        return normalized

    @field_validator("description", mode="before")
    @classmethod
    def normalize_description(cls, value: object) -> str:
        if value is None:
            return ""
        if not isinstance(value, str):
            raise ValueError("description must be a string")  # noqa: TRY004
        return value.strip()

    @model_validator(mode="after")
    def fill_and_validate_ai_model_type(self) -> AIDataSetCreateContract:
        allowed_by_dataset_type: dict[str, set[AIModelType]] = {
            "image": {"image_multilabel_classification", "phi_region_detector"},
            "video": {"video_segment_classification"},
        }
        if self.ai_model_type not in allowed_by_dataset_type[self.dataset_type]:
            raise ValueError("ai_model_type is not compatible with dataset_type")
        return self


class AIDataSetAttachVideoContract(BaseModel):
    """Canonical request for explicit or bulk dataset annotation attachment."""

    model_config = ConfigDict(extra="forbid", strict=True)

    video_id: int | None = Field(default=None, ge=1)
    frame_annotation_ids: list[int] = Field(default_factory=list)
    segment_ids: list[int] = Field(default_factory=list)
    include_all_annotations: bool = False
    include_frame_annotations: bool = False
    include_video_annotations: bool = False
    information_source_names: list[str] = Field(default_factory=list)

    @field_validator("information_source_names", mode="before")
    @classmethod
    def normalize_information_source_names(
        cls, value: list[str] | str | None
    ) -> list[str] | None:
        if value in (None, ""):
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("information_source_names")
    @classmethod
    def strip_information_source_names(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]

    @field_validator("frame_annotation_ids", "segment_ids")
    @classmethod
    def validate_positive_identifiers(cls, value: list[int]) -> list[int]:
        if any(identifier < 1 for identifier in value):
            raise ValueError("identifiers must be positive")
        return value

    @model_validator(mode="after")
    def validate_bulk_selection(self) -> AIDataSetAttachVideoContract:
        if not self.include_all_annotations:
            return self
        if self.video_id is not None or self.frame_annotation_ids or self.segment_ids:
            raise ValueError(
                "include_all_annotations cannot be combined with "
                "video_id, frame_annotation_ids, or segment_ids."
            )
        if not (self.include_frame_annotations or self.include_video_annotations):
            raise ValueError("At least one annotation type must be selected.")
        return self


class AIDataSetAttachmentResultContract(BaseModel):
    """Canonical result for explicit or bulk dataset annotation attachment."""

    model_config = ConfigDict(extra="forbid", strict=True)

    dataset_id: int = Field(ge=1)
    video_id: int | None = Field(default=None, ge=1)
    frame_annotation_count: int = Field(default=0, ge=0)
    video_annotation_count: int = Field(default=0, ge=0)
    attached_frame_annotation_count: int = Field(default=0, ge=0)
    attached_segment_count: int = Field(default=0, ge=0)
    attached_frame_annotation_ids: list[int] = Field(default_factory=list)
    attached_segment_ids: list[int] = Field(default_factory=list)

    @field_validator("attached_frame_annotation_ids", "attached_segment_ids")
    @classmethod
    def validate_positive_identifiers(cls, value: list[int]) -> list[int]:
        if any(identifier < 1 for identifier in value):
            raise ValueError("identifiers must be positive")
        return value


class AIModelTrainingRunContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    run_id: UUID
    run_key: str
    dataset_id: int
    dataset_name: str
    dataset_type: str = ""
    ai_model_type: str = ""

    backbone_name: str
    feature_mode: str
    freeze_backbone: bool
    epochs: int
    batch_size: int
    labelset_version: int
    treat_unlabeled_as_negative: bool
    backbone_checkpoint: str

    request_payload: JsonObject = Field(default_factory=dict)
    command_kwargs: JsonObject = Field(default_factory=dict)

    status: TrainingRunStatus
    server_instance_id: str = ""
    result: JsonObject
    artifact_paths: dict[str, str] = Field(default_factory=dict)
    error: str = ""
    stdout: str = ""
    stderr: str = ""

    created_at: datetime
    updated_at: datetime
    started_at: datetime
    finished_at: datetime

    is_terminal: bool = False


class AIModelTrainingRunCreateContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_id: int
    training_target: str = "image_multilabel"

    backbone_name: str = "resnet50_imagenet"
    feature_mode: str = "freeze_backbone"
    epochs: int = 10
    batch_size: int = 32
    labelset_version: int = 1
    device: str = "auto"
    annotation_source_scope: str = "all"
    treat_unlabeled_as_negative: bool = True
    backbone_checkpoint: str

    @field_validator("epochs", "batch_size", "labelset_version")
    @classmethod
    def validate_positive_int(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("value must be positive")
        return value


class AIModelTrainingRunUpdateContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: TrainingRunStatus | None = None
    result: JsonObject | None = None
    artifact_paths: dict[str, str] | None = None
    error: str | None = None
    stdout: str | None = None
    stderr: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class AIDataSetExportArtifactContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    artifact_id: UUID
    artifact_key: str
    dataset_id: int
    dataset_name: str
    dataset_type: str = ""
    ai_model_type: str = ""

    request_payload: JsonObject = Field(default_factory=dict)
    center_key: str
    all_centers: bool = False
    only_validated: bool = True

    status: ExportArtifactStatus
    output_path: str = ""
    download_filename: str = ""
    sha256: str = ""
    byte_size: int = 0
    summary: JsonObject = Field(default_factory=dict)
    error: str = ""

    created_at: datetime
    updated_at: datetime
    finished_at: datetime

    @field_validator("sha256")
    @classmethod
    def validate_sha256_or_blank(cls, value: str) -> str:
        if value and len(value) != 64:
            raise ValueError("sha256 must be blank or exactly 64 characters")
        return value


class AIDataSetExportCreateContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_id: int
    ai_dataset_name: str
    ai_dataset_type: DatasetType
    center_key: str
    all_centers: bool = False
    only_validated: bool = True

    @field_validator("center_key", "ai_dataset_name", mode="before")
    @classmethod
    def blank_to_none(cls, value: str | float | bool | None) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            return value.strip() or None
        converted = str(value).strip()
        return converted or None

    @model_validator(mode="after")
    def validate_dataset_selector(self) -> AIDataSetExportCreateContract:
        has_id = self.dataset_id
        has_name_type = bool(self.ai_dataset_name and self.ai_dataset_type)
        if not has_id and not has_name_type:
            raise ValueError(
                "Provide dataset_id or both ai_dataset_name and ai_dataset_type."
            )
        return self

    @model_validator(mode="after")
    def validate_center_scope(self) -> AIDataSetExportCreateContract:
        if self.center_key and self.all_centers:
            raise ValueError("Use center_key or all_centers, not both.")
        return self


class AITrainingManifestBuildContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label_set_id: int
    treat_unlabeled_as_negative: bool = False
    include_file_paths: bool = False
    check_frame_format: bool = True
    preprocessing_strategy: Literal[
        "preserve_dimensions_black_mask",
        "crop_to_endoscope_roi",
    ] = "preserve_dimensions_black_mask"
    recommended_model_input_strategy: Literal[
        "preserve_dimensions_black_mask",
        "crop_to_endoscope_roi",
    ] = "crop_to_endoscope_roi"
    information_source_names: list[str]

    @field_validator("information_source_names", mode="before")
    @classmethod
    def normalize_information_source_names(
        cls, value: list[str] | str | None
    ) -> list[str] | None:
        if value in (None, ""):
            return None
        if isinstance(value, str):
            names = [item.strip() for item in value.split(",") if item.strip()]
            return names or None
        return value


class AIDataSetStandardExportScopeContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    center_key: str
    all_centers: bool = False
    only_validated: bool = False

    @field_validator("center_key", mode="before")
    @classmethod
    def normalize_center_key(cls, value: str | float | bool | None) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            return value.strip() or None
        return str(value).strip() or None

    @model_validator(mode="after")
    def validate_scope(self) -> AIDataSetStandardExportScopeContract:
        if self.center_key and self.all_centers:
            raise ValueError("Use center_key or all_centers, not both.")
        return self


# Backward-compatible public aliases expected by endoreg_db.
AIDataSetActiveLearningConfigContract = AIDataSetActiveLearningConfigContractContract
AIDataSetActiveLearningCandidateContract = (
    AIDataSetActiveLearningCandidateContractContract
)
