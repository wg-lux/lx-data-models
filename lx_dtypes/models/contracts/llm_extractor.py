from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from lx_dtypes.models.contracts.text_anonymization import LLMMetadataPayload


class LLMModelEntryPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    name: str


class LLMModelCatalogEntryPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    id: str


class LLMOllamaModelsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    models: list[LLMModelEntryPayload] = Field(default_factory=list)


class LLMVllmModelsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    data: list[LLMModelCatalogEntryPayload] = Field(default_factory=list)


class LLMMetadataCacheStatsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    hit_count: int
    miss_count: int
    hit_rate: float
    cache_size: int
    max_size: int


class LLMModelInfoPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    current_model: str | None = None
    available_models: list[str] = Field(default_factory=list)
    total_models: int = 0
    cache_stats: LLMMetadataCacheStatsPayload | None = None


class LLMFrameDataPayload(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)

    frame_index: int = 0
    timestamp: float = 0.0
    ocr_text: str = ""
    ocr_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    has_text: bool = False
    has_patient_info: bool = False
    has_ui_elements: bool = False
    is_endoscopy_view: bool = False
    quality_score: float = Field(default=0.5, ge=0.0, le=1.0)
    frame_id: int | None = None
    frame_number: int | None = None

    def normalized_frame_index(self, fallback: int) -> int:
        if self.frame_number is not None:
            return self.frame_number
        if self.frame_id is not None:
            return self.frame_id
        return fallback


class LLMFrameContextPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    total_frames: int = 0
    text_frames: int = 0
    quality_scores: list[float] = Field(default_factory=list)
    timestamps: list[float] = Field(default_factory=list)
    frame_types: dict[str, int] = Field(default_factory=dict)


class LLMTextTimelineEntryPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    frame_index: int
    timestamp: float
    text_snippet: str
    confidence: float = Field(ge=0.0, le=1.0)


class LLMTemporalAnalysisPayload(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)

    duration_analysis: dict[str, float] = Field(default_factory=dict)
    text_appearance_timeline: list[LLMTextTimelineEntryPayload] = Field(
        default_factory=list
    )
    stability_scores: dict[str, float] = Field(default_factory=dict)
    change_points: list[int] = Field(default_factory=list)


class LLMEnrichedMetadataPayload(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)

    llm_extracted: LLMMetadataPayload = Field(default_factory=LLMMetadataPayload)
    frame_context: LLMFrameContextPayload = Field(
        default_factory=LLMFrameContextPayload
    )
    temporal_analysis: LLMTemporalAnalysisPayload = Field(
        default_factory=LLMTemporalAnalysisPayload
    )
    confidence_scores: dict[str, float] = Field(default_factory=dict)
    source_frames: list[LLMFrameDataPayload] = Field(default_factory=list)


class LLMEvaluationResultPayload(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)

    data_sources_used: list[str] = Field(default_factory=list)
    confidence_comparison: dict[str, float] = Field(default_factory=dict)
    data_completeness: float = 0.0


__all__ = [
    "LLMEnrichedMetadataPayload",
    "LLMEvaluationResultPayload",
    "LLMFrameContextPayload",
    "LLMFrameDataPayload",
    "LLMMetadataCacheStatsPayload",
    "LLMModelCatalogEntryPayload",
    "LLMModelEntryPayload",
    "LLMModelInfoPayload",
    "LLMOllamaModelsPayload",
    "LLMTemporalAnalysisPayload",
    "LLMTextTimelineEntryPayload",
    "LLMVllmModelsPayload",
]
