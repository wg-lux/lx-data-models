from __future__ import annotations

from datetime import date, time
from pathlib import Path
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    field_validator,
    model_validator,
)


FrameCleanerSource = Literal["frame_extraction"]
FrameObservationSourceTag = Literal[
    "ocr_roi",
    "east_ocr",
    "metadata_signal",
    "phi_detector",
]


class VideoRoiBox(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: int = Field(ge=0)
    y: int = Field(ge=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)


class VideoOcrRoi(RootModel[dict[str, VideoRoiBox]]):
    @field_validator("root")
    @classmethod
    def require_named_roi(cls, value: dict[str, VideoRoiBox]) -> dict[str, VideoRoiBox]:
        if not value:
            raise ValueError("At least one named ROI is required.")
        return value


class VideoPhiRegion(VideoRoiBox):
    source: Literal["phi_detector"]
    x1: int = Field(ge=0)
    y1: int = Field(ge=0)
    x2: int = Field(ge=0)
    y2: int = Field(ge=0)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    class_id: int | str | None = None

    @field_validator("x2")
    @classmethod
    def validate_x2(cls, value: int, info: Any) -> int:
        x1 = info.data.get("x1")
        if x1 is not None and value < x1:
            raise ValueError("x2 must be greater than or equal to x1.")
        return value

    @field_validator("y2")
    @classmethod
    def validate_y2(cls, value: int, info: Any) -> int:
        y1 = info.data.get("y1")
        if y1 is not None and value < y1:
            raise ValueError("y2 must be greater than or equal to y1.")
        return value

    @model_validator(mode="after")
    def validate_dimensions_match_corners(self) -> "VideoPhiRegion":
        if self.width != self.x2 - self.x1:
            raise ValueError("width must equal x2 - x1.")
        if self.height != self.y2 - self.y1:
            raise ValueError("height must equal y2 - y1.")
        return self


class FrameCleanerAccumulatedMeta(BaseModel):
    """Metadata dictionary initialized and merged inside FrameCleaner."""

    model_config = ConfigDict(extra="allow")

    file_path: str
    first_name: str | None = None
    last_name: str | None = None
    dob: date | str | None = None
    casenumber: str | None = None
    gender: str | None = None
    examination_date: date | str | None = None
    examination_time: time | str | None = None
    examiner_first_name: str | None = None
    examiner_last_name: str | None = None
    center: str | None = None
    endoscope_type: str | None = None
    endoscope_sn: str | None = None
    text: str | None = None
    source: FrameCleanerSource = "frame_extraction"


class FrameObservation(BaseModel):
    """Per-sampled-frame observation appended by FrameCleaner."""

    model_config = ConfigDict(extra="forbid")

    frame_number: int | None = Field(default=None, ge=0)
    frame_id: int | None = Field(default=None, ge=0)
    image_width: int = Field(gt=0)
    image_height: int = Field(gt=0)
    ocr_roi: VideoOcrRoi | None = None
    ocr_text: str = ""
    ocr_confidence: float = Field(ge=0.0, le=1.0)
    metadata_signal: bool
    is_sensitive: bool
    phi_regions: list[VideoPhiRegion] = Field(default_factory=list)
    source_tags: list[FrameObservationSourceTag] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_frame_identifiers_match(self) -> "FrameObservation":
        if (
            self.frame_id is not None
            and self.frame_number is not None
            and self.frame_id != self.frame_number
        ):
            raise ValueError("frame_id and frame_number must match.")
        return self


class FrameCollectionItem(BaseModel):
    """OCR frame candidate kept for video-level LLM enrichment."""

    model_config = ConfigDict(extra="forbid")

    frame_id: int | None = Field(default=None, ge=0)
    frame_number: int | None = Field(default=None, ge=0)
    ocr_text: str
    ocr_confidence: float = Field(ge=0.0, le=1.0)
    meta: dict[str, Any] = Field(default_factory=dict)
    is_sensitive: bool
    phi_regions: list[VideoPhiRegion] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_frame_identifiers_match(self) -> "FrameCollectionItem":
        if (
            self.frame_id is not None
            and self.frame_number is not None
            and self.frame_id != self.frame_number
        ):
            raise ValueError("frame_id and frame_number must match.")
        return self


class FrameAnalysisResult(BaseModel):
    """Return contract for FrameCleaner._analyze_video_frames."""

    model_config = ConfigDict(extra="forbid")

    accumulated: FrameCleanerAccumulatedMeta
    sensitive_idx: list[int] = Field(default_factory=list)
    best_ocr_text: str = ""
    best_ocr_conf: float = Field(default=-1.0, ge=-1.0, le=1.0)
    frames_processed: int = Field(ge=0)

    @field_validator("sensitive_idx")
    @classmethod
    def validate_sensitive_idx(cls, value: list[int]) -> list[int]:
        if any(frame_idx < 0 for frame_idx in value):
            raise ValueError("Frame indices must be non-negative.")
        return value


class FrameProcessResult(BaseModel):
    """Strict result returned by frame-level OCR and sensitivity processing."""

    model_config = ConfigDict(extra="forbid")

    is_sensitive: bool
    metadata: dict[str, Any] = Field(default_factory=dict)
    ocr_text: str = ""
    ocr_confidence: float = Field(ge=0.0, le=1.0)

    def as_legacy_tuple(self) -> tuple[bool, dict[str, Any], str, float]:
        return (
            self.is_sensitive,
            self.metadata,
            self.ocr_text,
            self.ocr_confidence,
        )


class VideoFormatProbe(BaseModel):
    """Subset of video_utils.detect_video_format consumed by FrameCleaner."""

    model_config = ConfigDict(extra="allow")

    has_audio: bool = True
    video_codec: str | None = None
    pixel_format: str | None = None
    width: int | None = Field(default=None, ge=0)
    height: int | None = Field(default=None, ge=0)
    container: str | None = None
    can_stream_copy: bool | None = None


class FrameRemovalPlan(BaseModel):
    """Validated frame-removal execution plan."""

    model_config = ConfigDict(extra="forbid")

    original_video: Path
    output_video: Path
    frames_to_remove: list[int] = Field(default_factory=list)
    total_frames: int | None = Field(default=None, ge=0)
    use_named_pipe: bool = True
    ffmpeg_timeout: int = Field(ge=1)

    @field_validator("frames_to_remove")
    @classmethod
    def validate_frames_to_remove(cls, value: list[int]) -> list[int]:
        if any(frame_idx < 0 for frame_idx in value):
            raise ValueError("Frame indices must be non-negative.")
        return sorted(set(value))

    @property
    def should_use_named_pipe(self) -> bool:
        frame_count = self.total_frames or 1000
        return self.use_named_pipe and len(self.frames_to_remove) < frame_count * 0.1


class FrameRemovalFilterArgs(BaseModel):
    """FFmpeg filter args and temporary filter scripts."""

    model_config = ConfigDict(extra="forbid")

    vf_args: list[str] = Field(default_factory=list)
    af_args: list[str] = Field(default_factory=list)
    filter_script_paths: list[Path] = Field(default_factory=list)


class VideoAnonymizerProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0"
    anonymizer_version: str = "unknown"
    detector_sources: list[str] = Field(default_factory=list)
    model_names: list[str] = Field(default_factory=list)
    model_versions: dict[str, str] = Field(default_factory=dict)
    proposal_counts: dict[str, int] = Field(default_factory=dict)


class VideoMeta(BaseModel):
    """Final video metadata payload produced by FrameCleaner.clean_video."""

    model_config = ConfigDict(extra="allow")

    file_path: str | None = None
    examination_date: date | str | None = None
    examination_time: time | str | None = None
    casenumber: str | None = None
    pseudo_patient: str | None = None
    pseudo_examination: str | None = None
    gender: str | None = None
    pseudo_examiners: str | list[str] | None = None
    first_name: str | None = None
    last_name: str | None = None
    dob: date | str | None = None
    endoscope_type: str | None = None
    endoscope_sn: str | None = None
    examiner_first_name: str | None = None
    examiner_last_name: str | None = None
    center: str | None = None
    text: str | None = None
    anonymized_text: str | None = None
    external_id: str | None = None
    frame_observations: list[FrameObservation] = Field(default_factory=list)
    anonymizer_provenance: VideoAnonymizerProvenance | None = None


__all__ = [
    "FrameAnalysisResult",
    "FrameCleanerAccumulatedMeta",
    "FrameCleanerSource",
    "FrameCollectionItem",
    "FrameProcessResult",
    "FrameRemovalFilterArgs",
    "FrameRemovalPlan",
    "FrameObservation",
    "FrameObservationSourceTag",
    "VideoAnonymizerProvenance",
    "VideoFormatProbe",
    "VideoMeta",
    "VideoOcrRoi",
    "VideoPhiRegion",
    "VideoRoiBox",
]
